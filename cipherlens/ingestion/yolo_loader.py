"""YOLO dataset ingestion loader.

Parses YOLO format txt annotations and corresponding images into
DatasetItem instances, gracefully degrading on malformed files.
"""

import logging
from pathlib import Path
from PIL import Image

from cipherlens.ingestion.unified_schema import (
    AcquisitionMeta,
    Annotation,
    DatasetItem,
)
from cipherlens.utils.hashing import sha256_digest
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_yolo_dataset(
    image_dir: str | Path,
    annotation_dir: str | Path,
    class_names: list[str],
    contributor_id: str = "unknown",
    batch_id: str = "default_batch",
) -> tuple[list[DatasetItem], int]:
    """Load a YOLO dataset from directories.

    Args:
        image_dir: Directory containing images.
        annotation_dir: Directory containing .txt annotation files.
        class_names: List of class names, where index matches class_id.
        contributor_id: ID of the contributor.
        batch_id: ID of the batch.

    Returns:
        A tuple of (valid_dataset_items, skipped_count).
    """
    img_dir = Path(image_dir)
    ann_dir = Path(annotation_dir)
    
    if not img_dir.exists():
        logger.error("Image directory not found: %s", img_dir)
        return [], 0
        
    items: list[DatasetItem] = []
    skipped_count = 0
    
    # Supported image extensions
    img_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    img_files = [f for f in img_dir.iterdir() if f.suffix.lower() in img_extensions]
    
    for img_path in img_files:
        try:
            # Read and hash image content
            with open(img_path, "rb") as img_file:
                content = img_file.read()
                img_sha256 = sha256_digest(content)
                
            # Attempt to determine dimensions (YOLO txt format has normalized coords,
            # so we need image dimensions if we were to convert them, though our schema
            # stores what's given. We will record real dims).
            try:
                with Image.open(img_path) as pil_img:
                    width, height = pil_img.size
            except Exception:
                width, height = 0, 0
                
            item_id = sha256_digest(f"{img_path.name}_{contributor_id}".encode("utf-8"))
            
            # Look for corresponding annotation
            ann_path = ann_dir / f"{img_path.stem}.txt"
            item_annotations = []
            
            if ann_path.exists():
                with open(ann_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        if len(parts) < 5:
                            logger.warning("Skipping malformed annotation line in %s", ann_path)
                            continue
                            
                        cat_id = int(parts[0])
                        cat_name = class_names[cat_id] if 0 <= cat_id < len(class_names) else "unknown"
                        
                        # YOLO format: [x_center, y_center, width, height] normalized
                        # Unified schema expects xywh. We store as provided (normalized).
                        try:
                            bbox = [float(p) for p in parts[1:5]]
                        except ValueError:
                            logger.warning("Invalid bbox float in %s", ann_path)
                            continue
                            
                        item_annotations.append(
                            Annotation(
                                category_id=cat_id,
                                category_name=cat_name,
                                bbox_xywh=bbox,
                                segmentation=None
                            )
                        )
            
            acq_meta = AcquisitionMeta(timestamp=None, sensor=None, notes=None)
            
            items.append(
                DatasetItem(
                    item_id=item_id,
                    image_path=img_path.name,
                    image_sha256=img_sha256,
                    width=width,
                    height=height,
                    annotations=item_annotations,
                    contributor_id=contributor_id,
                    batch_id=batch_id,
                    source_format="YOLO",
                    acquisition_meta=acq_meta,
                )
            )
        except Exception as e:
            logger.warning("Skipping malformed or missing image record %s: %s", img_path.name, e)
            skipped_count += 1
            
    return items, skipped_count
