"""Access tier resolution for model integrity checks.

Determines whether the provided model supports WHITE_BOX or BLACK_BOX analysis.
"""

from cipherlens.ingestion.unified_schema import ModelHandle
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def determine_access_tier(model_handle: ModelHandle, override: str | None = None) -> str:
    """Decide the access tier for the model.

    Args:
        model_handle: The loaded model and its manifest.
        override: Optional manual override ("WHITE_BOX" or "BLACK_BOX").

    Returns:
        "WHITE_BOX" or "BLACK_BOX".
    """
    if override in {"WHITE_BOX", "BLACK_BOX"}:
        logger.info("Using manual override for access_tier: %s", override)
        return override
        
    tier = model_handle.manifest.access_tier_available
    if tier not in {"WHITE_BOX", "BLACK_BOX"}:
        logger.warning("Unknown access_tier '%s', defaulting to BLACK_BOX", tier)
        return "BLACK_BOX"
        
    return tier
