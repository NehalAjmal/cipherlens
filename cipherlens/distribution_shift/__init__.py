"""Distribution Shift Module.

Aggregates MMD, KS tests, and Energy-OOD checks.
"""

from cipherlens.distribution_shift.energy_ood import check_energy_ood, compute_energy_scores
from cipherlens.distribution_shift.ks_test import check_ks_drift
from cipherlens.distribution_shift.mmd import check_mmd, compute_mmd2
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)

def analyze(ref_embeddings, test_embeddings, test_image_paths) -> list[Finding]:
    """Execute all distribution shift checks.
    
    Args:
        ref_embeddings: The embeddings of the reference/training dataset.
        test_embeddings: The embeddings of the test dataset.
        test_image_paths: The file paths of the test dataset images.
        
    Returns:
        A list of unified Finding objects.
    """
    logger.info("Starting Distribution Shift analysis...")
    findings = []
    findings.extend(check_mmd(ref_embeddings, test_embeddings))
    findings.extend(check_ks_drift(ref_embeddings, test_embeddings))
    findings.extend(check_energy_ood(test_image_paths))
    return findings

__all__ = [
    "analyze",
    "check_energy_ood",
    "compute_energy_scores",
    "check_ks_drift",
    "check_mmd",
    "compute_mmd2",
]
