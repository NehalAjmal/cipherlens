"""STRIP (Black-Box) Model Integrity check.

Detects backdoors by perturbing inputs and measuring the entropy
of the model's predictions. Backdoored inputs exhibit low entropy
even under strong perturbations.
"""

import numpy as np
import scipy.stats

from cipherlens.config import get_config
from cipherlens.ingestion.unified_schema import ModelHandle
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_strip_battery(model_handle: ModelHandle, n_perturbations: int) -> tuple[float, float]:
    """Run a black-box perturbation battery on the model.
    
    For the MVP, this simulates STRIP by feeding random noise as perturbed
    inputs and measuring the entropy of the outputs.
    
    Args:
        model_handle: The loaded model.
        n_perturbations: Number of perturbed samples to test.
        
    Returns:
        Tuple of (mean_entropy, median_entropy).
    """
    entropies = []
    
    if model_handle.manifest.format == "PYTORCH":
        try:
            import torch
            import torch.nn.functional as F
        except ImportError:
            return 1.0, 1.0
            
        model = model_handle.model_obj
        if not hasattr(model, "eval"):
            return 1.0, 1.0
            
        model.eval()
        with torch.no_grad():
            for _ in range(n_perturbations):
                # Dummy input simulating a perturbed image (1, 3, 224, 224)
                dummy_input = torch.randn(1, 3, 224, 224)
                try:
                    out = model(dummy_input)
                    probs = F.softmax(out, dim=1).cpu().numpy()[0]
                    # Calculate Shannon entropy
                    ent = scipy.stats.entropy(probs)
                    entropies.append(ent)
                except Exception as e:
                    logger.debug("STRIP dummy pass failed: %s", e)
                    break
                    
    elif model_handle.manifest.format == "ONNX":
        session = model_handle.model_obj
        try:
            input_name = session.get_inputs()[0].name
            input_shape = session.get_inputs()[0].shape
            
            # Resolve dynamic batch sizes to 1
            shape = [1 if isinstance(dim, str) or dim is None else dim for dim in input_shape]
            if len(shape) != 4:
                shape = [1, 3, 224, 224] # fallback
                
            for _ in range(n_perturbations):
                dummy_input = np.random.randn(*shape).astype(np.float32)
                out = session.run(None, {input_name: dummy_input})[0][0]
                
                # Softmax
                exp_out = np.exp(out - np.max(out))
                probs = exp_out / np.sum(exp_out)
                
                ent = scipy.stats.entropy(probs)
                entropies.append(ent)
        except Exception as e:
            logger.debug("STRIP ONNX dummy pass failed: %s", e)
            
    if not entropies:
        return 1.0, 1.0
        
    return float(np.mean(entropies)), float(np.median(entropies))


def check_strip(model_handle: ModelHandle, access_tier: str) -> list[Finding]:
    """Run STRIP black-box battery.

    Args:
        model_handle: The loaded model.
        access_tier: "WHITE_BOX" or "BLACK_BOX". STRIP runs in both, 
                     but is the primary defense in BLACK_BOX.

    Returns:
        List of Findings.
    """
    config = get_config()
    n_perturbations = config.thresholds.strip_perturbation_grid
    
    logger.info("Running STRIP perturbation battery...")
    mean_ent, median_ent = run_strip_battery(model_handle, n_perturbations)
    
    findings = []
    
    # In STRIP, a clean model will have high entropy for random perturbed inputs.
    # A backdoored model will have near-zero entropy if a trigger is present.
    # Since we are using pure random noise (which doesn't contain a trigger),
    # a true negative should yield high entropy.
    # We flag if entropy is suspiciously low (e.g., < 0.5 nats).
    
    if median_ent < 0.5:
        findings.append(
            Finding(
                category="MODEL_BACKDOOR",
                severity="HIGH",
                confidence=0.8,
                reason="STRIP battery detected abnormally low entropy under strong perturbations.",
                evidence={
                    "strip_mean_entropy": mean_ent,
                    "strip_median_entropy": median_ent,
                    "threshold": 0.5,
                },
                affected_elements=[model_handle.manifest.model_id],
                access_tier=access_tier,
            )
        )
        
    return findings
