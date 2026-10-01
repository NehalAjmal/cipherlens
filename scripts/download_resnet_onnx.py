import torch
import torchvision.models as models
from pathlib import Path

out_dir = Path("data/samples")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "resnet50_clean.onnx"

print(f"Downloading ResNet50 and exporting to {out_path}...")

model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
model.eval()
dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(model, dummy_input, str(out_path), opset_version=14)

print("Export complete.")
