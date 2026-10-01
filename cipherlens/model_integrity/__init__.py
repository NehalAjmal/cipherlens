"""Model Integrity Module.

Aggregates findings from white-box and black-box backdoor detection techniques.
"""

from cipherlens.ingestion.unified_schema import ModelHandle
from cipherlens.model_integrity.access_tier import determine_access_tier
from cipherlens.model_integrity.neural_cleanse import check_neural_cleanse
from cipherlens.model_integrity.strip import check_strip
from cipherlens.model_integrity.weight_checks import check_weights
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def analyze(model_handle: ModelHandle, override_tier: str | None = None) -> list[Finding]:
    """Execute model integrity checks based on available access tier.

    Args:
        model_handle: The loaded model to analyze.
        override_tier: Optional manual override ("WHITE_BOX" or "BLACK_BOX").

    Returns:
        A list of unified Finding objects.
    """
    access_tier = determine_access_tier(model_handle, override_tier)
    logger.info("Starting Model Integrity analysis with tier: %s", access_tier)
    
    findings: list[Finding] = []
    
    findings.extend(check_neural_cleanse(model_handle, access_tier))
    findings.extend(check_strip(model_handle, access_tier))
    findings.extend(check_weights(model_handle, access_tier))
    
    return findings

__all__ = ["analyze", "determine_access_tier"]
