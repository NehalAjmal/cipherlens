"""Activation Clustering anomaly detection.

Clusters embeddings into two groups (clean vs poison) and flags
classes where a cluster is highly distinct and anomalous.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from cipherlens.data_integrity.backbone import embed
from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_activation_clustering(dataset_items: list[DatasetItem], images_dir: str) -> list[Finding]:
    """Detect activation clustering anomalies in a dataset.

    Groups images by category, embeds them, reduces dimensionality with PCA,
    and clusters into two groups to find potential poison clusters.

    Args:
        dataset_items: List of DatasetItem instances.
        images_dir: Base directory for the images.

    Returns:
        A list of Finding objects.
    """
    if not dataset_items:
        return []

    items_by_cat: dict[str, list[DatasetItem]] = {}
    for item in dataset_items:
        cats = {ann.category_name for ann in item.annotations}
        for cat in cats:
            items_by_cat.setdefault(cat, []).append(item)

    findings: list[Finding] = []

    for cat_name, items in items_by_cat.items():
        if len(items) < 4:
            continue

        image_paths = [f"{images_dir}/{item.image_path}" for item in items]
        item_ids = [item.item_id for item in items]

        embeddings = embed(image_paths)
        if len(embeddings) == 0:
            continue
            
        # PCA to reduce noise before clustering (common in AC)
        n_components = min(10, len(embeddings), embeddings.shape[1])
        pca = PCA(n_components=n_components)
        try:
            reduced = pca.fit_transform(embeddings)
        except Exception as e:
            logger.warning("PCA failed for class '%s': %s", cat_name, e)
            continue

        # KMeans into 2 clusters
        kmeans = KMeans(n_clusters=2, n_init=10, random_state=42)
        try:
            clusters = kmeans.fit_predict(reduced)
        except Exception as e:
            logger.warning("KMeans failed for class '%s': %s", cat_name, e)
            continue

        # Basic anomaly check: if one cluster is significantly smaller
        # than the other, it might be a poison cluster.
        # We flag if min_cluster_size <= 35% of total
        c0_size = np.sum(clusters == 0)
        c1_size = np.sum(clusters == 1)
        total = len(clusters)
        
        min_size = min(c0_size, c1_size)
        anomalous_cluster = 0 if c0_size < c1_size else 1
        
        # If the smaller cluster is < 35% of the data, flag it
        if min_size / total <= 0.35:
            outlier_indices = np.where(clusters == anomalous_cluster)[0]
            affected_ids = [item_ids[i] for i in outlier_indices]
            
            finding = Finding(
                category="DATA_POISONING",
                severity="MEDIUM",
                confidence=0.7,
                reason=f"Activation clustering found a distinct minority cluster in class '{cat_name}'",
                evidence={
                    "cluster_ratio": float(min_size / total),
                    "minority_size": int(min_size),
                    "total_size": int(total),
                    "class": cat_name,
                },
                affected_elements=affected_ids,
            )
            findings.append(finding)

    return findings
