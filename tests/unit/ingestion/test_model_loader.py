"""Unit tests for the model loader."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import onnx

from cipherlens.ingestion.model_loader import load_model


def test_load_pytorch_enforces_weights_only():
    """Verify that PyTorch models are loaded safely with weights_only=True."""
    with tempfile.NamedTemporaryFile(suffix=".pt") as tmp:
        tmp.write(b"dummy")
        tmp.flush()
        
        with patch("cipherlens.ingestion.model_loader.torch.load") as mock_load:
            with patch("cipherlens.ingestion.sandbox.run_in_docker_sandbox"):
                # We must mock torch.load to return a dummy so it doesn't fail parsing
                mock_load.return_value = "dummy_model"
                
                model = load_model(tmp.name, model_id="test_model")
                
                mock_load.assert_called_once_with(Path(tmp.name), weights_only=True, map_location="cpu")
                assert model.manifest.format == "PYTORCH"


def test_load_onnx_enforces_checker():
    """Verify that ONNX models are checked before being returned."""
    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        tmp.write(b"dummy")
        tmp.flush()
        
        with patch("cipherlens.ingestion.model_loader.onnx.load") as mock_load:
            with patch("cipherlens.ingestion.model_loader.onnx.checker.check_model") as mock_check:
                with patch("cipherlens.ingestion.model_loader.ort.InferenceSession") as mock_ort:
                    with patch("cipherlens.ingestion.sandbox.run_in_docker_sandbox"):
                        mock_model = type("MockONNX", (), {"graph": type("MockGraph", (), {"initializer": []})()})
                        mock_load.return_value = mock_model
                        
                        model = load_model(tmp.name, model_id="test_model")
                        
                        mock_load.assert_called_once()
                        mock_check.assert_called_once_with(mock_model)
                        mock_ort.assert_called_once()
                        assert model.manifest.format == "ONNX"


def test_load_onnx_fails_validation():
    """Verify that ONNX model failing check raises an error."""
    with tempfile.NamedTemporaryFile(suffix=".onnx") as tmp:
        tmp.write(b"dummy")
        tmp.flush()
        
        with patch("cipherlens.ingestion.model_loader.onnx.load"):
            with patch("cipherlens.ingestion.model_loader.onnx.checker.check_model") as mock_check:
                mock_check.side_effect = onnx.checker.ValidationError("Invalid ONNX")
                
                with patch("cipherlens.ingestion.sandbox.run_in_docker_sandbox"):
                    with pytest.raises(ValueError, match="ONNX model failed validation"):
                        load_model(tmp.name, model_id="test_model")


def test_safe_torch_load_blocks_malicious_pickle(tmp_path: Path):
    """Verify that safe_torch_load blocks live malicious-pickle execution without code execution."""
    import os
    import torch
    from cipherlens.ingestion.model_loader import safe_torch_load

    class MaliciousPayload:
        def __reduce__(self):
            return (os.system, ("touch /tmp/cipherlens_pwned_safe_load.txt",))

    malicious_file = tmp_path / "malicious_payload.pt"
    torch.save(MaliciousPayload(), malicious_file)

    breadcrumb = Path("/tmp/cipherlens_pwned_safe_load.txt")
    if breadcrumb.exists():
        breadcrumb.unlink()

    # Attempting to load with safe_torch_load MUST reject the unsafe payload
    with pytest.raises(Exception):
        safe_torch_load(malicious_file)

    # Assert that host was completely protected and exploit never ran
    assert not breadcrumb.exists(), "Exploit was executed! safe_torch_load failed to protect host."


def test_safe_torch_load_succeeds_for_clean_weights(tmp_path: Path):
    """Verify that safe_torch_load successfully loads clean weights."""
    import torch
    from cipherlens.ingestion.model_loader import safe_torch_load

    clean_file = tmp_path / "clean_weights.pt"
    weights = {"layer.weight": torch.tensor([1.0, 2.0, 3.0])}
    torch.save(weights, clean_file)

    loaded = safe_torch_load(clean_file)
    assert "layer.weight" in loaded
    assert torch.equal(loaded["layer.weight"], weights["layer.weight"])

