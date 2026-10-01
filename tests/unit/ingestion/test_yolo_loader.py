"""Unit tests for YOLO loader."""

import tempfile
from pathlib import Path

import pytest

from cipherlens.ingestion.yolo_loader import load_yolo_dataset


@pytest.fixture
def yolo_setup():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        img_dir = tmp_path / "images"
        ann_dir = tmp_path / "labels"
        img_dir.mkdir()
        ann_dir.mkdir()
        
        # Valid image and valid annotation
        valid_img = img_dir / "valid.jpg"
        valid_img.write_bytes(b"dummy image data")
        valid_ann = ann_dir / "valid.txt"
        valid_ann.write_text("0 0.5 0.5 0.2 0.2\n")
        
        # Valid image but malformed annotation file (not crash, just skipped line)
        img2 = img_dir / "bad_ann.jpg"
        img2.write_bytes(b"dummy image data")
        ann2 = ann_dir / "bad_ann.txt"
        ann2.write_text("0 invalid_float 0.5 0.2 0.2\n1 0.1 0.1 0.1 0.1\n")
        
        # Malformed image file simulating a read error (e.g. permission error),
        # Here we just check the loader doesn't crash if something goes wrong. We can't easily simulate a read error.
        # But we can check it processes valid files correctly.
        
        yield img_dir, ann_dir


def test_load_yolo_graceful_degradation(yolo_setup):
    """Verify that YOLO loader skips malformed annotations instead of crashing."""
    img_dir, ann_dir = yolo_setup
    class_names = ["person", "car"]
    
    items, skipped_count = load_yolo_dataset(img_dir, ann_dir, class_names)
    
    assert len(items) == 2
    assert skipped_count == 0
    
    # Sort items by image path for predictable checks
    items.sort(key=lambda x: x.image_path)
    
    # bad_ann.jpg should have 1 annotation (the valid one)
    assert items[0].image_path == "bad_ann.jpg"
    assert len(items[0].annotations) == 1
    assert items[0].annotations[0].category_name == "car"  # class 1
    
    # valid.jpg should have 1 annotation
    assert items[1].image_path == "valid.jpg"
    assert len(items[1].annotations) == 1
    assert items[1].annotations[0].category_name == "person"  # class 0
