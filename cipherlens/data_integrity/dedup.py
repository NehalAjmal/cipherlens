"""Deduplication and Near-Duplicate detection.

Identifies near-duplicate images using cosine distance on backbone embeddings,
flagging potential data leakage or over-representation.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_distances

from cipherlens.config import get_config
from cipherlens.data_integrity.backbone import embed
from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_duplicates(dataset_items: list[DatasetItem], images_dir: str) -> list[Finding]:
    """Detect near-duplicate images in the dataset.

    Args:
        dataset_items: List of DatasetItem instances.
        images_dir: Base directory for the images.

    Returns:
        A list of Finding objects.
    """
    if not dataset_items:
        return []

    config = get_config()
    threshold = config.thresholds.dedup_cosine_distance_max

    image_paths = [f"{images_dir}/{item.image_path}" for item in dataset_items]
    item_ids = [item.item_id for item in dataset_items]

    # Batch embedding
    embeddings = embed(image_paths)
    if len(embeddings) == 0:
        return []

    findings: list[Finding] = []
    
    # Compute pairwise cosine distances
    dists = cosine_distances(embeddings)
    
    # Find pairs below threshold (upper triangle to avoid dupes)
    # dists is shape (N, N)
    n = len(embeddings)
    
    # Fast vectorized search instead of pure python double loop
    np.fill_diagonal(dists, float('inf'))
    indices = np.where(np.triu(dists <= threshold, k=1))
    
    for idx in range(len(indices[0])):
        i, j = indices[0][idx], indices[1][idx]
        finding = Finding(
            category="NEAR_DUPLICATE",
            severity="LOW",
            confidence=1.0 - float(dists[i, j]),
            reason=f"Near-duplicate images detected (distance {dists[i,j]:.4f} <= {threshold})",
            evidence={
                "cosine_distance": float(dists[i, j]),
                "threshold": float(threshold)
            },
            affected_elements=[item_ids[i], item_ids[j]],
        )
        findings.append(finding)

    return findings
