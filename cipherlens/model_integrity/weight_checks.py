"""Weight and Activation Checks (White-Box).

Examines the model's weight matrices for spectral norm anomalies
and measures activation kurtosis to identify suspicious sparse pathways.
"""

import numpy as np
import scipy.stats

from cipherlens.ingestion.unified_schema import ModelHandle
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_weights(model_handle: ModelHandle, access_tier: str) -> list[Finding]:
    """Run spectral norm ratio and activation kurtosis checks.

    Args:
        model_handle: The loaded model.
        access_tier: "WHITE_BOX" or "BLACK_BOX".

    Returns:
        List of Findings.
    """
    if access_tier != "WHITE_BOX":
        # Gracefully skip in black box
        return []
        
    try:
        import torch
    except ImportError:
        return []

    model = model_handle.model_obj
    if not isinstance(model, torch.nn.Module):
        return []

    findings = []
    
    # 1. Spectral Norm Ratio Check
    # Ratio of largest singular value to the mean of singular values
    max_snr = 0.0
    layer_with_max = "None"
    
    for name, module in model.named_modules():
        if isinstance(module, (torch.nn.Linear, torch.nn.Conv2d)):
            with torch.no_grad():
                weight = module.weight.view(module.weight.shape[0], -1)
                if weight.shape[0] < 2 or weight.shape[1] < 2:
                    continue
                    
                # Compute singular values
                # SVD is expensive, we do it only if matrix isn't huge, or use torch.linalg.svdvals
                # To be safe/fast for MVP, we take a subset or just run it on small layers.
                try:
                    s = torch.linalg.svdvals(weight.float())
                    snr = float(s[0] / (s.mean() + 1e-6))
                    if snr > max_snr:
                        max_snr = snr
                        layer_with_max = name
                except Exception:
                    pass

    # Threshold for SNR is typically around 10-20 for clean models, higher for poisoned
    if max_snr > 30.0:
        findings.append(
            Finding(
                category="MODEL_BACKDOOR",
                severity="MEDIUM",
                confidence=0.7,
                reason=f"High spectral norm ratio ({max_snr:.2f}) detected in layer '{layer_with_max}'",
                evidence={"spectral_norm_ratio": max_snr, "layer": layer_with_max},
                affected_elements=[model_handle.manifest.model_id],
                access_tier=access_tier,
            )
        )
        
    # 2. Activation Kurtosis Check
    # High kurtosis indicates sparse, heavy-tailed activations often seen in backdoors.
    # We use a dummy input and a forward hook to capture one layer's activations.
    kurtosis_val = 0.0
    
    # Find a good intermediate layer (e.g. ReLU or BatchNorm)
    target_module = None
    for module in reversed(list(model.modules())):
        if isinstance(module, torch.nn.ReLU):
            target_module = module
            break
            
    if target_module is not None:
        activations = []
        
        def hook(m, inp, out):
            activations.append(out.detach().cpu().numpy())
            
        handle = target_module.register_forward_hook(hook)
        
        model.eval()
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224)
            try:
                model(dummy_input)
                if activations:
                    flat_acts = activations[0].flatten()
                    kurt = float(scipy.stats.kurtosis(flat_acts))
                    kurtosis_val = kurt
            except Exception as e:
                logger.debug("Kurtosis dummy pass failed: %s", e)
                
        handle.remove()
        
        # Normal kurtosis for Gaussian is 0 (Fisher definition), high positive means heavy tails
        if kurtosis_val > 10.0:
            findings.append(
                Finding(
                    category="MODEL_BACKDOOR",
                    severity="LOW",
                    confidence=0.6,
                    reason=f"Abnormally high activation kurtosis ({kurtosis_val:.2f})",
                    evidence={"activation_kurtosis": kurtosis_val},
                    affected_elements=[model_handle.manifest.model_id],
                    access_tier=access_tier,
                )
            )

    return findings
