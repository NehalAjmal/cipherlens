"""Integration tests for the full CipherLens pipeline."""

import json
from pathlib import Path

import pytest

from cipherlens.pipeline import run_pipeline


@pytest.fixture(scope="module")
def clean_model_path():
    """Path to the cached ResNet-18 model."""
    return str(Path("models_cache/backbone/resnet18.pt").resolve())


def test_pipeline_model_only(clean_model_path):
    """Test the pipeline degrades gracefully when given only a model."""
    
    if not Path(clean_model_path).exists():
        pytest.skip("Reference backbone not found.")

    from unittest import mock
    with mock.patch("cipherlens.ingestion.sandbox.run_in_docker_sandbox"):
        report = run_pipeline(
            model_path=clean_model_path,
            model_format="PYTORCH"
        )
    
    assert report is not None
    assert "report_id" in report
    assert "overall_disposition" in report
    
    # Check that it executed model checks (no crash) and is a valid report
    # Since it's a clean model state_dict, we expect 0 backdoor findings.
    
    # Asset metadata should reflect the model
    assert report["asset_metadata"]["asset_type"] == "MODEL"
    assert report["access_tier"] == "WHITE_BOX"
    
    # And there should be no data poisoning findings since no dataset was provided
    assert not any(f["category"] == "DATA_POISONING" for f in report["findings"])


def test_pipeline_dataset_only():
    """Test the pipeline degrades gracefully when given only a dataset."""
    
    dataset_path = Path("data/samples/annotations/instances_samples.json")
    images_dir = Path("data/samples/images")
    
    if not dataset_path.exists() or not images_dir.exists():
        pytest.skip("COCO sample data not found.")
        
    report = run_pipeline(
        dataset_path=str(dataset_path),
        images_dir=str(images_dir),
        dataset_format="COCO"
    )
    
    assert report is not None
    assert "report_id" in report
    
    # Asset metadata should reflect the dataset
    assert report["asset_metadata"]["asset_type"] == "DATASET"
    
    # Should have data findings but no model findings
    assert len(report["findings"]) > 0
    assert not any(f["category"] == "MODEL_BACKDOOR" for f in report["findings"])
