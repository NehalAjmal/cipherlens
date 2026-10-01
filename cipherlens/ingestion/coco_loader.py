"""COCO dataset ingestion loader.

Parses COCO format JSON files into DatasetItem instances, gracefully
degrading and skipping malformed records.
"""

import json
import logging
from pathlib import Path
from typing import Any

from cipherlens.ingestion.unified_schema import (
    AcquisitionMeta,
    Annotation,
    DatasetItem,
)
from cipherlens.utils.hashing import sha256_digest
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_coco_dataset(
    annotation_path: str | Path,
    image_dir: str | Path,
    contributor_id: str = "unknown",
    batch_id: str = "default_batch",
) -> tuple[list[DatasetItem], int]:
    """Load a COCO dataset from a JSON annotation file.

    Args:
        annotation_path: Path to the COCO JSON.
        image_dir: Directory containing the corresponding images.
        contributor_id: ID of the contributor.
        batch_id: ID of the batch.

    Returns:
        A tuple of (valid_dataset_items, skipped_count).
    """
    ann_path = Path(annotation_path)
    img_dir = Path(image_dir)
    
    if not ann_path.exists():
        logger.error("Annotation file not found: %s", ann_path)
        return [], 0
        
    try:
        with open(ann_path, "r", encoding="utf-8") as f:
            coco_data = json.load(f)
    except Exception as e:
        logger.error("Failed to parse COCO JSON %s: %s", ann_path, e)
        return [], 0
        
    categories = {
        cat["id"]: cat["name"]
        for cat in coco_data.get("categories", [])
    }
    
    # Map image_id -> [annotations]
    annotations_by_img: dict[int, list[dict[str, Any]]] = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann.get("image_id")
        if img_id is not None:
            annotations_by_img.setdefault(img_id, []).append(ann)
            
    items: list[DatasetItem] = []
    skipped_count = 0
    
    for img in coco_data.get("images", []):
        try:
            # Must have minimal valid fields
            if "file_name" not in img or "id" not in img:
                raise ValueError("Missing file_name or id")
                
            img_path = img_dir / img["file_name"]
            if not img_path.exists():
                raise FileNotFoundError(f"Image {img_path} not found")
                
            # Read and hash image content
            with open(img_path, "rb") as img_file:
                content = img_file.read()
                img_sha256 = sha256_digest(content)
                
            item_id = sha256_digest(f"{img['file_name']}_{contributor_id}".encode("utf-8"))
            
            # Parse annotations
            item_annotations = []
            for raw_ann in annotations_by_img.get(img["id"], []):
                cat_id = raw_ann.get("category_id", -1)
                cat_name = categories.get(cat_id, "unknown")
                bbox = raw_ann.get("bbox")
                
                if not isinstance(bbox, list) or len(bbox) != 4:
                    # Skip malformed annotations but keep the image
                    continue
                    
                item_annotations.append(
                    Annotation(
                        category_id=cat_id,
                        category_name=cat_name,
                        bbox_xywh=bbox,
                        segmentation=raw_ann.get("segmentation")
                    )
                )
                
            acq_meta = AcquisitionMeta(
                timestamp=img.get("date_captured"),
                sensor=None,
                notes=None
            )
            
            items.append(
                DatasetItem(
                    item_id=item_id,
                    image_path=img["file_name"],
                    image_sha256=img_sha256,
                    width=img.get("width", 0),
                    height=img.get("height", 0),
                    annotations=item_annotations,
                    contributor_id=contributor_id,
                    batch_id=batch_id,
                    source_format="COCO",
                    acquisition_meta=acq_meta,
                )
            )
        except Exception as e:
            logger.warning("Skipping malformed or missing image record %s: %s", img.get('id', 'unknown'), e)
            skipped_count += 1
            
    return items, skipped_count
