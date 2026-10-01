"""Backbone loader for the Data Integrity module.

Loads the cached frozen backbone (ResNet-18) and provides an
embedding function for images.
"""

from pathlib import Path
from PIL import Image

import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms

from cipherlens.config import get_config
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)

# Global cached model
_MODEL = None
_TRANSFORM = None
_DEVICE = None


def _get_device() -> torch.device:
    config = get_config()
    device_str = config.execution.device
    if device_str == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA requested but not available. Falling back to CPU.")
        device_str = "cpu"
    return torch.device(device_str)


def _init_backbone():
    global _MODEL, _TRANSFORM, _DEVICE
    if _MODEL is not None:
        return
        
    config = get_config()
    backbone_dir = Path(config.paths.backbone_cache)
    model_path = backbone_dir / "resnet18.pt"
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Backbone not found at {model_path}. Run scripts/download_reference_backbone.py first."
        )
        
    _DEVICE = _get_device()
    
    logger.info("Loading reference backbone from %s to %s", model_path, _DEVICE)
    model = models.resnet18(weights=None)
    
    # SECURITY INVARIANT: weights_only=True
    state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    
    # Remove the classification head (fc layer) to get embeddings
    # ResNet-18 fc is the last layer. We replace it with Identity.
    model.fc = torch.nn.Identity()
    
    model.to(_DEVICE)
    model.eval()
    
    _MODEL = model
    
    # Standard ImageNet transforms required by ResNet
    _TRANSFORM = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def embed(image_paths: list[str | Path]) -> np.ndarray:
    """Extract embeddings for a batch of images using the frozen backbone.

    Args:
        image_paths: List of file paths to the images.

    Returns:
        A numpy array of shape (N, D) where N is the number of images
        and D is the embedding dimension (512 for ResNet-18).
    """
    _init_backbone()
    
    batch = []
    for path in image_paths:
        try:
            # Convert to RGB to ensure 3 channels
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                tensor = _TRANSFORM(img_rgb)
                batch.append(tensor)
        except Exception as e:
            logger.error("Failed to process image %s for embedding: %s", path, e)
            # If an image fails, provide a zero vector to maintain batch size
            # In a real system we'd handle this better, but for MVP returning zeros is safe
            batch.append(torch.zeros(3, 224, 224))
            
    if not batch:
        return np.array([])
        
    batch_tensor = torch.stack(batch).to(_DEVICE)
    
    with torch.no_grad():
        embeddings = _MODEL(batch_tensor)
        
    return embeddings.cpu().numpy()
