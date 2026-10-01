import fiftyone as fo
import fiftyone.zoo as foz

# Target classes suitable for stop-sign / vehicle backdoor scenarios
CLASSES = ["person", "car", "stop sign"]
SAMPLE_COUNT = 100

print(f"Downloading {SAMPLE_COUNT} COCO validation samples for {CLASSES}...")

# 1. Download targeted slice directly from COCO 2017 validation split
dataset = foz.load_zoo_dataset(
    "coco-2017",
    split="validation",
    label_types=["detections"],
    classes=CLASSES,
    max_samples=SAMPLE_COUNT,
)

# 2. Export into standard COCO JSON format
dataset.export(
    export_dir="data/raw/coco/",
    dataset_type=fo.types.COCODetectionDataset,
    classes=CLASSES,
)

print("Download complete. Saved to data/raw/coco/")
