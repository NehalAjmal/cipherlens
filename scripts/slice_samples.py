import json
import shutil
from pathlib import Path

raw_dir = Path("data/raw/coco")
samples_img_dir = Path("data/samples/images")
samples_ann_dir = Path("data/samples/annotations")

samples_img_dir.mkdir(parents=True, exist_ok=True)
samples_ann_dir.mkdir(parents=True, exist_ok=True)

# Load full export annotations
with open(raw_dir / "labels.json", "r") as f:
    coco_data = json.load(f)

# Pick the first 20 images
selected_images = coco_data["images"][:20]
selected_image_ids = {img["id"] for img in selected_images}

# Copy the image files
for img in selected_images:
    src = raw_dir / "data" / img["file_name"]
    dst = samples_img_dir / img["file_name"]
    if src.exists():
        shutil.copy2(src, dst)

# Filter matching annotations
selected_annotations = [
    ann for ann in coco_data["annotations"]
    if ann["image_id"] in selected_image_ids
]

sample_coco = {
    "info": coco_data.get("info", {}),
    "licenses": coco_data.get("licenses", []),
    "categories": coco_data["categories"],
    "images": selected_images,
    "annotations": selected_annotations,
}

with open(samples_ann_dir / "instances_samples.json", "w") as f:
    json.dump(sample_coco, f, indent=2)

print(f"Prepared data/samples/ with {len(selected_images)} images and {len(selected_annotations)} annotations.")
