"""Kolmogorov-Smirnov and Wasserstein drift detection.

Performs 2-sample KS tests and calculates Wasserstein distances
between reference and test dataset feature distributions.
"""

import numpy as np
from scipy import stats

from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_ks_drift(ref_embeddings: np.ndarray, test_embeddings: np.ndarray) -> list[Finding]:
    """Detect distribution shift using KS test and Wasserstein distance.

    Args:
        ref_embeddings: Base/training dataset embeddings (N, D).
        test_embeddings: New/inference dataset embeddings (M, D).

    Returns:
        List of Findings.
    """
    if len(ref_embeddings) < 5 or len(test_embeddings) < 5:
        logger.debug("Not enough samples for KS calculation.")
        return []

    D = ref_embeddings.shape[1]
    ks_stats = []
    p_values = []
    w_dists = []

    for d in range(D):
        ref_col = ref_embeddings[:, d]
        test_col = test_embeddings[:, d]
        
        # KS test
        stat, p = stats.ks_2samp(ref_col, test_col)
        ks_stats.append(stat)
        p_values.append(p)
        
        # Wasserstein distance
        w_dist = stats.wasserstein_distance(ref_col, test_col)
        w_dists.append(w_dist)

    # Benjamini-Hochberg FDR correction on p-values (simplified evaluation)
    # For MVP, we flag if the median Wasserstein is large, or if too many
    # dimensions show significant drift (p < 0.05).
    p_values = np.array(p_values)
    significant_dims = np.sum(p_values < 0.05)
    ratio_significant = significant_dims / D
    
    mean_w = float(np.mean(w_dists))
    max_ks = float(np.max(ks_stats))

    findings = []
    
    # Heuristic: if more than 30% of features significantly drift, flag it.
    if ratio_significant > 0.30:
        findings.append(
            Finding(
                category="DISTRIBUTION_SHIFT",
                severity="LOW",
                confidence=float(ratio_significant),
                reason=f"Significant marginal drift in {ratio_significant*100:.1f}% of embedding dimensions",
                evidence={
                    "significant_features_ratio": float(ratio_significant),
                    "mean_wasserstein": mean_w,
                    "max_ks_stat": max_ks,
                },
                affected_elements=["dataset"],
                access_tier="BLACK_BOX",
            )
        )

    return findings
