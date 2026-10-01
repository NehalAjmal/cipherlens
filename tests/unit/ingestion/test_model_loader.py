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
