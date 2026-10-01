"""Energy-based Out-Of-Distribution (OOD) score detection.

Calculates the energy score of samples to detect adversarial
perturbations and severe out-of-distribution shifts.
"""

from pathlib import Path

import numpy as np

from cipherlens.config import get_config
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)

# Cache for the classification model
_CLS_MODEL = None
_TRANSFORM = None
_DEVICE = None


def _init_classifier():
    global _CLS_MODEL, _TRANSFORM, _DEVICE
    if _CLS_MODEL is not None:
        return
        
    try:
        import torch
        import torchvision.models as models
        import torchvision.transforms as transforms
    except ImportError:
        logger.error("PyTorch required for Energy OOD.")
        return
        
    config = get_config()
    backbone_dir = Path(config.paths.backbone_cache)
    model_path = backbone_dir / "resnet18.pt"
    
    if not model_path.exists():
        logger.error("Backbone not found at %s", model_path)
        return
        
    device_str = config.execution.device
    if device_str == "cuda" and not torch.cuda.is_available():
        device_str = "cpu"
    _DEVICE = torch.device(device_str)
    
    # Load ResNet-18 WITH classification head for logits
    model = models.resnet18(weights=None)
    state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    
    model.to(_DEVICE)
    model.eval()
    
    _CLS_MODEL = model
    
    _TRANSFORM = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def compute_energy_scores(image_paths: list[str | Path]) -> np.ndarray:
    """Compute energy scores for a batch of images.
    
    Args:
        image_paths: List of file paths to the images.
        
    Returns:
        Numpy array of energy scores. Lower energy means IN-distribution,
        higher energy means OUT-of-distribution.
    """
    _init_classifier()
    if _CLS_MODEL is None:
        return np.array([])
        
    try:
        from PIL import Image
        import torch
    except ImportError:
        return np.array([])

    config = get_config()
    T = config.thresholds.energy_ood_temperature
    
    batch = []
    valid_indices = []
    
    for i, path in enumerate(image_paths):
        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                tensor = _TRANSFORM(img_rgb)
                batch.append(tensor)
                valid_indices.append(i)
        except Exception as e:
            logger.warning("Failed to process image %s: %s", path, e)
            
    if not batch:
        return np.array([])
        
    batch_tensor = torch.stack(batch).to(_DEVICE)
    
    with torch.no_grad():
        logits = _CLS_MODEL(batch_tensor)
        
        # Energy: E(x) = -T * log(sum(exp(logit / T)))
        # To avoid overflow in exp, we use logsumexp trick
        # E(x) = -T * (max_logit/T + log(sum(exp((logit - max_logit)/T))))
        max_logits = torch.max(logits, dim=1, keepdim=True)[0]
        exp_term = torch.exp((logits - max_logits) / T)
        log_sum_exp = max_logits.squeeze() / T + torch.log(torch.sum(exp_term, dim=1))
        
        energies = -T * log_sum_exp
        
    return energies.cpu().numpy()


def check_energy_ood(test_image_paths: list[str | Path]) -> list[Finding]:
    """Check dataset for adversarial/OOD samples using Energy scores.

    Args:
        test_image_paths: List of images to check.

    Returns:
        List of Findings.
    """
    if not test_image_paths:
        return []
        
    energies = compute_energy_scores(test_image_paths)
    if len(energies) == 0:
        return []
        
    # Anomaly threshold for energy:
    # Typical in-distribution energies might be -10 to -20 (negative).
    # OOD energies are closer to 0 or positive.
    # We will flag if a substantial portion of the batch has high energy,
    # or just return the median energy if doing batch-level drift.
    
    median_energy = float(np.median(energies))
    
    # We'll use a conservative threshold for the MVP, or flag if it's very anomalous
    # For now, we mainly expose the score. If it's above -2.0, we consider it highly OOD.
    threshold = -2.0
    
    findings = []
    if median_energy > threshold:
        findings.append(
            Finding(
                category="DISTRIBUTION_SHIFT",
                severity="HIGH",
                confidence=0.8,
                reason=f"Energy-OOD detects adversarial/OOD signatures (median energy {median_energy:.2f} > {threshold})",
                evidence={
                    "median_energy": median_energy,
                    "max_energy": float(np.max(energies)),
                    "threshold": threshold,
                },
                affected_elements=["dataset"],
                access_tier="BLACK_BOX",
            )
        )
        
    return findings
