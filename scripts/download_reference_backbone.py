"""Script to download and cache a reference backbone model.

Downloads ResNet-18 from torchvision and saves it to models_cache/backbone/.
"""

import os
from pathlib import Path

import torch
import torchvision.models as models

from cipherlens.utils.hashing import sha256_digest


def main():
    print("Downloading reference backbone (ResNet-18)...")
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    
    # We only need the state dict for inference/embedding extraction
    state_dict = model.state_dict()
    
    out_dir = Path("models_cache/backbone")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "resnet18.pt"
    
    print(f"Saving to {out_path}...")
    torch.save(state_dict, out_path)
    
    with open(out_path, "rb") as f:
        digest = sha256_digest(f.read())
        
    print(f"Done. SHA-256: {digest}")


if __name__ == "__main__":
    main()
