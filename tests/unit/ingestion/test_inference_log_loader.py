"""Unit tests for the inference log loader."""

import tempfile
from pathlib import Path

import pytest

from cipherlens.ingestion.inference_log_loader import load_inference_logs


@pytest.fixture
def log_setup():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        # Write 3 lines: 1 valid, 1 missing a key, 1 invalid JSON
        tmp.write(b'{"record_id": "r1", "timestamp_utc": "2024", "image_path": "a.jpg", "model_id": "m1", "config_hash": "c1", "outputs": []}\n')
        tmp.write(b'{"record_id": "r2", "image_path": "b.jpg"}\n')  # Malformed: missing fields
        tmp.write(b'this is not json\n')
        tmp.flush()
        
        yield tmp.name


def test_load_inference_logs_graceful_degradation(log_setup):
    """Verify inference logs degrade gracefully and skip malformed lines."""
    records, skipped_count = load_inference_logs(log_setup)
    
    assert len(records) == 1
    assert records[0].record_id == "r1"
    
    assert skipped_count == 2


def test_load_inference_logs_arrow(tmp_path: Path):
    """Verify PyArrow zero-copy ingestion of valid inference log records."""
    import json
    from cipherlens.ingestion.inference_log_loader import load_inference_logs_arrow

    log_file = tmp_path / "valid_batch.jsonl"
    with open(log_file, "w") as f:
        f.write(json.dumps({"record_id": "r1", "timestamp_utc": "2024", "image_path": "a.jpg", "model_id": "m1", "config_hash": "c1", "outputs": []}) + "\n")
        f.write(json.dumps({"record_id": "r2", "timestamp_utc": "2024", "image_path": "b.jpg", "model_id": "m1", "config_hash": "c1", "outputs": []}) + "\n")

    table = load_inference_logs_arrow(log_file)
    assert len(table) == 2

