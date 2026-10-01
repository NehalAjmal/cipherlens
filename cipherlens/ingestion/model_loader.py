"""Model loader for the ingestion layer.

Safely loads PyTorch and ONNX models per AI_RULES.md security invariants:
- PyTorch: always uses `weights_only=True`
- ONNX: always runs `onnx.checker.check_model` before returning
Produces unified ModelHandle objects matching BACKEND_SCHEMA.md §3.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import onnx
import onnxruntime as ort
import torch

from cipherlens.ingestion.unified_schema import ModelHandle, ModelManifest
from cipherlens.utils.hashing import sha256_digest
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_model(
    model_path: str | Path,
    model_id: str,
    architecture_hint: str = "unknown",
    access_tier_available: str = "BLACK_BOX",
) -> ModelHandle:
    """Load a PyTorch or ONNX model safely and construct its manifest.

    Args:
        model_path: Path to the .pt, .pth, or .onnx file.
        model_id: Identifier for the model.
        architecture_hint: Hint about the model architecture (e.g., 'resnet50').
        access_tier_available: WHITE_BOX or BLACK_BOX.

    Returns:
        A ModelHandle wrapping the loaded model and its manifest.

    Raises:
        ValueError: If the model format is unsupported or fails security checks.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    # Compute SHA-256 of the model file
    with open(path, "rb") as f:
        file_sha256 = sha256_digest(f.read())

    ext = path.suffix.lower()
    
    loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    manifest = ModelManifest(
        model_id=model_id,
        format="UNKNOWN",
        file_path=str(path),
        sha256=file_sha256,
        architecture_hint=architecture_hint,
        num_parameters=None,
        loaded_at=loaded_at,
        access_tier_available=access_tier_available,
    )

    if ext in {".pt", ".pth"}:
        manifest.format = "PYTORCH"
        
        from cipherlens.ingestion.sandbox import is_sandboxing_available, run_in_docker_sandbox
        
        if is_sandboxing_available():
            try:
                run_in_docker_sandbox(path, "PYTORCH")
                logger.info("Sandbox pre-validation passed. Proceeding with host deserialization.")
            except Exception as e:
                logger.error("Sandbox execution blocked loading: %s", e)
                raise ValueError(f"Sandboxing blocked model load (likely malicious): {e}") from e
        else:
            logger.warning("Sandboxing unavailable, falling back to safe-deserialization-only.")
            
        try:
            # SECURITY INVARIANT: weights_only=True is mandatory for torch.load
            model_obj = torch.load(path, weights_only=True, map_location="cpu")
            
            # If it's a state dict, we don't have the architecture to compute parameters easily
            # If it's a full model, we can try
            if isinstance(model_obj, torch.nn.Module):
                manifest.num_parameters = sum(p.numel() for p in model_obj.parameters())
                
        except Exception as e:
            logger.error("Failed to load PyTorch model safely: %s", e)
            raise ValueError(f"Failed to load PyTorch model: {e}") from e

    elif ext == ".onnx":
        manifest.format = "ONNX"
        try:
            # SECURITY INVARIANT: Must check ONNX model before creating InferenceSession
            onnx_model = onnx.load(str(path))
            onnx.checker.check_model(onnx_model)
            
            # Count parameters roughly from initializers
            num_params = sum(
                tensor.dims[0] if len(tensor.dims) == 1 else tensor.dims[0] * (tensor.dims[1] if len(tensor.dims) > 1 else 1) # Crude approximation
                for tensor in onnx_model.graph.initializer
            )
            # A more robust counting would multiply all dims
            num_params = 0
            for tensor in onnx_model.graph.initializer:
                p = 1
                for d in tensor.dims:
                    p *= d
                num_params += p
            manifest.num_parameters = num_params
            
            # Create inference session
            model_obj = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            
        except onnx.checker.ValidationError as e:
            logger.error("ONNX model failed security checker validation: %s", e)
            raise ValueError(f"ONNX model failed validation: {e}") from e
        except Exception as e:
            logger.error("Failed to load ONNX model: %s", e)
            raise ValueError(f"Failed to load ONNX model: {e}") from e
            
    else:
        raise ValueError(f"Unsupported model extension: {ext}")

    return ModelHandle(manifest=manifest, model_obj=model_obj)
