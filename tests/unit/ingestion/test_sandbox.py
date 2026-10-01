import os
import pytest
import torch
from pathlib import Path
from unittest import mock

from cipherlens.ingestion.model_loader import load_model


class MaliciousPayload:
    def __reduce__(self):
        # Attempt to create a file in the host system's /tmp directory
        return (os.system, ("touch /tmp/cipherlens_pwned.txt",))


def test_sandboxed_malicious_pickle_is_contained(tmp_path: Path):
    """Test that a malicious pickle is caught and contained by the Docker sandbox."""
    # 1. Create a malicious model
    malicious_path = tmp_path / "malicious.pt"
    
    # Save the payload
    torch.save(MaliciousPayload(), malicious_path)
    
    # Ensure the breadcrumb doesn't exist yet
    breadcrumb = Path("/tmp/cipherlens_pwned.txt")
    if breadcrumb.exists():
        breadcrumb.unlink()
        
    # 2. Try loading the model. 
    # If Docker is available, sandbox.py will run `torch.load(weights_only=False)`
    # inside the container, detonating the payload.
    # The payload will run `touch /tmp/cipherlens_pwned.txt` INSIDE the container.
    # We assert that the model load fails (because the sandbox catches the crash or times out,
    # or fails to return a valid object) AND that the host filesystem is not affected.
    
    from cipherlens.ingestion.sandbox import is_sandboxing_available
    
    if not is_sandboxing_available():
        pytest.skip("Docker is not available. Skipping sandbox containment test.")
        
    with pytest.raises(ValueError, match="Sandboxing blocked model load"):
        load_model(malicious_path, "malicious_model")
        
    # 3. Assert host is safe
    assert not breadcrumb.exists(), "Sandbox failed! Host system was compromised."


@mock.patch("cipherlens.ingestion.sandbox.is_sandboxing_available", return_value=False)
def test_fallback_when_sandbox_unavailable(mock_check, tmp_path: Path, caplog):
    """Test that the system gracefully falls back to safe deserialization if Docker is missing."""
    import logging
    
    # Create a benign model (just a simple state dict so weights_only=True allows it)
    safe_path = tmp_path / "safe.pt"
    torch.save({"weight": torch.randn(2, 2)}, safe_path)
    
    with caplog.at_level(logging.WARNING):
        handle = load_model(safe_path, "safe_model")
        
    assert handle.manifest.format == "PYTORCH"
    assert "Sandboxing unavailable, falling back to safe-deserialization-only" in caplog.text
