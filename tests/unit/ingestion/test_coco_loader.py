"""Unit tests for COCO loader."""

import json
import tempfile
from pathlib import Path

import pytest

from cipherlens.ingestion.coco_loader import load_coco_dataset


@pytest.fixture
def coco_setup():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        # Create a valid image
        valid_img = img_dir / "valid.jpg"
        valid_img.write_bytes(b"dummy image data")
        
        # Create a malformed COCO JSON
        # It contains 1 valid record, 1 record missing file_name, 1 record missing the physical file
        coco_json = {
            "categories": [{"id": 1, "name": "person"}],
            "images": [
                {"id": 1, "file_name": "valid.jpg"},
                {"id": 2},  # Malformed: missing file_name
                {"id": 3, "file_name": "missing.jpg"}  # Malformed: file doesn't exist
            ],
            "annotations": [
                {"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 10, 50, 50]},
                {"id": 2, "image_id": 1, "category_id": 1, "bbox": "invalid_bbox"}, # Malformed annotation, skips annot but keeps image
            ]
        }
        
        ann_path = tmp_path / "instances.json"
        with open(ann_path, "w") as f:
            json.dump(coco_json, f)
            
        yield ann_path, img_dir


def test_load_coco_graceful_degradation(coco_setup):
    """Verify that COCO loader skips malformed records instead of crashing."""
    ann_path, img_dir = coco_setup
    
    items, skipped_count = load_coco_dataset(ann_path, img_dir)
    
    # Expect 1 valid item (valid.jpg)
    assert len(items) == 1
    assert items[0].image_path == "valid.jpg"
    
    # 1 valid annotation (the invalid one is skipped)
    assert len(items[0].annotations) == 1
    assert items[0].annotations[0].bbox_xywh == [10, 10, 50, 50]
    
    # Expect 2 skipped items (missing file_name, missing physical file)
    assert skipped_count == 2
