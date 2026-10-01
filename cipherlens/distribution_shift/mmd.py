"""Maximum Mean Discrepancy (MMD) distribution shift detection.

Implements a hand-rolled multi-scale RBF-kernel MMD to detect drift
between two datasets without relying on heavy external ML frameworks.
"""

import numpy as np

from cipherlens.config import get_config
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def _rbf_kernel(X: np.ndarray, Y: np.ndarray, bandwidths: list[float]) -> np.ndarray:
    """Compute the multi-scale RBF kernel between X and Y."""
    # Compute squared Euclidean distances
    # ||x - y||^2 = ||x||^2 + ||y||^2 - 2(x . y)
    X_sq = np.sum(X ** 2, axis=1)[:, np.newaxis]
    Y_sq = np.sum(Y ** 2, axis=1)[np.newaxis, :]
    dist_sq = X_sq + Y_sq - 2 * np.dot(X, Y.T)
    # Clamp negative values due to floating point inaccuracies
    dist_sq = np.maximum(dist_sq, 0.0)
    
    # Sum of RBFs
    K = np.zeros_like(dist_sq)
    for bw in bandwidths:
        K += np.exp(-dist_sq / (2.0 * bw ** 2))
        
    return K


def compute_mmd2(X: np.ndarray, Y: np.ndarray, bandwidths: list[float]) -> float:
    """Compute the squared Maximum Mean Discrepancy between X and Y."""
    n = X.shape[0]
    m = Y.shape[0]
    
    if n == 0 or m == 0:
        return 0.0
        
    K_XX = _rbf_kernel(X, X, bandwidths)
    K_YY = _rbf_kernel(Y, Y, bandwidths)
    K_XY = _rbf_kernel(X, Y, bandwidths)
    
    # MMD^2 formula
    # E[K(X,X)] + E[K(Y,Y)] - 2E[K(X,Y)]
    # We remove the diagonal terms for an unbiased estimator, but for this
    # MVP standard biased estimator is perfectly fine and stable.
    mmd2 = np.mean(K_XX) + np.mean(K_YY) - 2 * np.mean(K_XY)
    return float(max(0.0, mmd2))


def check_mmd(ref_embeddings: np.ndarray, test_embeddings: np.ndarray) -> list[Finding]:
    """Detect distribution shift using MMD on feature embeddings.

    Args:
        ref_embeddings: Base/training dataset embeddings.
        test_embeddings: New/inference dataset embeddings.

    Returns:
        List of Findings.
    """
    config = get_config()
    bandwidths = config.thresholds.mmd_kernel_bandwidths
    
    if len(ref_embeddings) < 5 or len(test_embeddings) < 5:
        logger.debug("Not enough samples for MMD calculation.")
        return []

    mmd2 = compute_mmd2(ref_embeddings, test_embeddings, bandwidths)
    
    findings = []
    
    # A typical threshold would be determined by permutation testing,
    # but for MVP we use a static heuristic threshold or simply report it.
    # We will flag if MMD^2 > 0.05
    threshold = 0.05
    
    if mmd2 > threshold:
        findings.append(
            Finding(
                category="DISTRIBUTION_SHIFT",
                severity="MEDIUM",
                confidence=0.75,
                reason=f"Significant distribution shift detected via MMD (score: {mmd2:.4f})",
                evidence={
                    "mmd_squared_score": mmd2,
                    "threshold": threshold,
                    "bandwidths": bandwidths,
                },
                affected_elements=["dataset"],
                access_tier="BLACK_BOX",  # MMD operates on output embeddings
            )
        )

    return findings
