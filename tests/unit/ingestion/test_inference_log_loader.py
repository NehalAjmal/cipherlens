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
