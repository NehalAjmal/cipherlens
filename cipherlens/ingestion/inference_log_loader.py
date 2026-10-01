"""Inference log loader.

Parses .jsonl inference logs into InferenceRecord instances,
gracefully skipping malformed lines.
"""

import json
import logging
from pathlib import Path

from cipherlens.ingestion.unified_schema import InferenceRecord
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def load_inference_logs(log_path: str | Path) -> tuple[list[InferenceRecord], int]:
    """Load inference records from a JSONL file.

    Args:
        log_path: Path to the .jsonl file.

    Returns:
        A tuple of (valid_records, skipped_count).
    """
    path = Path(log_path)
    if not path.exists():
        logger.error("Inference log file not found: %s", path)
        return [], 0
        
    records: list[InferenceRecord] = []
    skipped_count = 0
    
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Check for required fields
                required_keys = {"record_id", "timestamp_utc", "image_path", "model_id", "config_hash", "outputs"}
                if not required_keys.issubset(data.keys()):
                    raise ValueError(f"Missing required keys. Found: {data.keys()}")
                    
                records.append(
                    InferenceRecord(
                        record_id=data["record_id"],
                        timestamp_utc=data["timestamp_utc"],
                        image_path=data["image_path"],
                        model_id=data["model_id"],
                        config_hash=data["config_hash"],
                        outputs=data["outputs"],
                    )
                )
            except Exception as e:
                logger.warning("Skipping malformed inference record at line %d in %s: %s", line_num, path.name, e)
                skipped_count += 1
                
    return records, skipped_count
