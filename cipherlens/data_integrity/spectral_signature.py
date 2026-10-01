"""Spectral Signature anomaly detection.

Identifies potential data poisoning by finding outlier embeddings
along the principal component of the image representations.
"""

import numpy as np

from cipherlens.config import get_config
from cipherlens.data_integrity.backbone import embed
from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_spectral_signatures(dataset_items: list[DatasetItem], images_dir: str) -> list[Finding]:
    """Detect spectral signature anomalies in a dataset.

    Groups images by their annotated categories, computes embeddings using the
    frozen backbone, and finds outliers along the top singular vector.

    Args:
        dataset_items: List of DatasetItem instances.
        images_dir: Base directory for the images.

    Returns:
        A list of Finding objects.
    """
    if not dataset_items:
        return []

    config = get_config()
    iqr_multiplier = config.thresholds.spectral_signature_iqr_multiplier

    # Group items by category. Since an image can have multiple boxes,
    # it might participate in multiple category evaluations.
    items_by_cat: dict[str, list[DatasetItem]] = {}
    for item in dataset_items:
        cats = {ann.category_name for ann in item.annotations}
        for cat in cats:
            items_by_cat.setdefault(cat, []).append(item)

    findings: list[Finding] = []

    for cat_name, items in items_by_cat.items():
        if len(items) < 3:
            logger.debug("Skipping spectral signature for class '%s' (not enough samples)", cat_name)
            continue

        image_paths = [f"{images_dir}/{item.image_path}" for item in items]
        item_ids = [item.item_id for item in items]

        # Get embeddings
        embeddings = embed(image_paths)
        if len(embeddings) == 0:
            continue

        # Compute centered embeddings
        mean_emb = np.mean(embeddings, axis=0)
        centered = embeddings - mean_emb

        # SVD to get top singular vector
        try:
            _, _, V = np.linalg.svd(centered, full_matrices=False)
            top_vec = V[0]
        except np.linalg.LinAlgError:
            logger.warning("SVD failed to converge for class '%s'", cat_name)
            continue

        # Projection scores
        scores = np.abs(np.dot(centered, top_vec))

        # Outlier detection using IQR
        q1 = np.percentile(scores, 25)
        q3 = np.percentile(scores, 75)
        iqr = q3 - q1
        threshold = q3 + iqr_multiplier * iqr

        outlier_indices = np.where(scores > threshold)[0]

        if len(outlier_indices) > 0:
            affected_ids = [item_ids[i] for i in outlier_indices]
            max_score = float(np.max(scores[outlier_indices]))
            
            finding = Finding(
                category="DATA_POISONING",
                severity="HIGH",
                confidence=0.8,
                reason=f"Spectral signature anomalies detected in class '{cat_name}'",
                evidence={
                    "spectral_anomaly_max": max_score,
                    "threshold": float(threshold),
                    "outlier_count": len(affected_ids),
                    "class": cat_name,
                },
                affected_elements=affected_ids,
            )
            findings.append(finding)

    return findings
