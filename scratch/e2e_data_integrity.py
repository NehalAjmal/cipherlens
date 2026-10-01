import sys
import pprint
from pathlib import Path
from cipherlens.ingestion.coco_loader import load_coco_dataset
from cipherlens.data_integrity import analyze

def test_e2e():
    ann_path = "data/samples/annotations/instances_samples.json"
    img_dir = "data/samples/images"
    
    print("Loading COCO dataset...")
    items, skipped = load_coco_dataset(ann_path, img_dir)
    print(f"Loaded {len(items)} items, skipped {skipped}.")
    
    print("Running Data Integrity checks...")
    findings = analyze(items, img_dir)
    
    print(f"Found {len(findings)} findings.")
    for f in findings:
        pprint.pprint(f.to_dict())

if __name__ == "__main__":
    test_e2e()
