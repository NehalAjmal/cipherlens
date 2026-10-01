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
    tier = model_handle.manifest.access_tier_available
    if tier not in {"WHITE_BOX", "BLACK_BOX"}:
        logger.warning("Unknown access_tier '%s', defaulting to BLACK_BOX", tier)
        tier = "BLACK_BOX"
        
    if override in {"WHITE_BOX", "BLACK_BOX"}:
        logger.info("Using manual override for access_tier: %s", override)
        tier = override
        
    # Phase 8: Intercept detectors before they reach white-box algorithms
    if tier == "WHITE_BOX" and model_handle.manifest.format == "PYTORCH" and model_handle.model_obj is not None:
        from cipherlens.model_integrity.detector_bridge import is_faster_rcnn, wrap_detector_if_needed
        import torch.nn as nn
        
        obj = model_handle.model_obj
        if isinstance(obj, nn.Module):
            # Is it a torchvision Faster R-CNN?
            if is_faster_rcnn(obj):
                logger.info("Supported Faster R-CNN detector found. Wrapping in surrogate for White-Box analysis.")
                model_handle.model_obj = wrap_detector_if_needed(obj)
            # Rough duck typing for other common detectors (YOLO, SSD, etc.)
            elif hasattr(obj, "names") and hasattr(obj, "yaml") or "yolo" in str(type(obj)).lower():
                logger.info("Unsupported detector architecture (YOLO/etc) detected. Downgrading to BLACK_BOX STRIP analysis.")
                tier = "BLACK_BOX"

    return tier
