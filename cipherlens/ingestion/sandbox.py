import os
import shutil
import subprocess
from pathlib import Path

from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def is_sandboxing_available() -> bool:
    """Check if Docker is installed and running."""
    if not shutil.which("docker"):
        return False
    try:
        # Check if docker daemon is reachable
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def run_in_docker_sandbox(model_path: Path, format_type: str) -> None:
    """Perform a dry-run load of the model file inside an isolated Docker container.
    
    The container has network access disabled and mounts the model file as read-only.
    If the file is a malicious pickle bomb, it will execute inside the container,
    fail to reach the network, and any filesystem destruction will be contained.
    
    Args:
        model_path: Path to the model file.
        format_type: "PYTORCH" or "ONNX".
        
    Raises:
        RuntimeError: If the sandbox execution fails (e.g., due to malicious activity).
    """
    abs_path = model_path.resolve()
    
    # We use a standard Python image for ONNX, but for PyTorch we need torch.
    # To avoid forcing a massive 5GB pytorch image pull on every run if not present,
    # we use python:3.11-slim. For PyTorch files, we extract the zip and parse the pickle.
    # Actually, using pytorch/pytorch:latest is the safest bet for a true representation.
    if format_type == "PYTORCH":
        image = "pytorch/pytorch:latest"
        # We load with weights_only=False in the sandbox to explicitly detonate any payload safely!
        cmd = f"python -c \"import torch; torch.load('{abs_path}', weights_only=False, map_location='cpu')\""
    elif format_type == "ONNX":
        image = "python:3.11-slim"
        cmd = f"pip install onnx && python -c \"import onnx; onnx.load('{abs_path}')\""
    else:
        return

    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none", # Total network isolation
        "-v", f"{abs_path}:{abs_path}:ro", # Read-only mount of the model
        image,
        "sh", "-c", cmd
    ]
    
    logger.info("Running sandboxed pre-validation for %s using %s", model_path.name, image)
    
    try:
        # We run it with a timeout. Malicious pickles might hang (e.g. while True).
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=30, # 30 seconds max for the load
            check=False
        )
        if result.returncode != 0:
            logger.error("Sandbox execution failed with code %d. Stderr: %s", result.returncode, result.stderr)
            raise RuntimeError(f"Sandboxed loading failed (possible malicious payload). Stderr: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("Sandbox execution timed out after 30s. Possible malicious payload or infinite loop.")
        raise RuntimeError("Sandboxed loading timed out.")
