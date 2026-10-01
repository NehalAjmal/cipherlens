"""Label Consistency detection.

Identifies potential LABEL_FLIP attacks by finding images with identical
hashes or very high similarity that have conflicting class labels.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_distances

from cipherlens.data_integrity.backbone import embed
from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_label_consistency(dataset_items: list[DatasetItem], images_dir: str) -> list[Finding]:
    """Detect label flips/inconsistencies among similar images.

    Args:
        dataset_items: List of DatasetItem instances.
        images_dir: Base directory for the images.

    Returns:
        A list of Finding objects.
    """
    if not dataset_items:
        return []

    findings: list[Finding] = []
    
    # 1. Check exact hash collisions with mismatched labels
    # Group by image_sha256
    hash_groups: dict[str, list[DatasetItem]] = {}
    for item in dataset_items:
        hash_groups.setdefault(item.image_sha256, []).append(item)
        
    for h, items in hash_groups.items():
        if len(items) > 1:
            # Check if their category sets differ
            first_cats = {ann.category_name for ann in items[0].annotations}
            for other in items[1:]:
                other_cats = {ann.category_name for ann in other.annotations}
                if first_cats != other_cats:
                    finding = Finding(
                        category="LABEL_FLIP",
                        severity="HIGH",
                        confidence=1.0,
                        reason="Identical images have conflicting labels",
                        evidence={
                            "image_sha256": h,
                            "labels_1": list(first_cats),
                            "labels_2": list(other_cats)
                        },
                        affected_elements=[items[0].item_id, other.item_id],
                    )
                    findings.append(finding)
                    
    # 2. We could also check near-duplicates with mismatched labels, 
    # but exact hash collisions are the strongest indicator of a targeted flip.
    
    return findings
