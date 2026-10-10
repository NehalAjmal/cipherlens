"""Red Team Scenario C: Tamper Inference Fixture Generator.

Demonstrates:
1. Altering any field post-signing reliably breaks the Ed25519 signature every time.
2. Direct out-of-band manipulation of record 2-of-3 in the Merkle ledger
   is localized to that exact index, not just flagged generically.
"""

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any

from cipherlens.provenance.crypto import (
    generate_keypair,
    generate_provenance_record,
    verify_provenance_record,
)
from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def simulate_field_tampering_attack() -> dict[str, Any]:
    """Demonstrate that tampering with any single field after signing breaks verification.

    Tests multiple fields independently (timestamp, actor_id, operation,
    inputs_hash, outputs_hash, config_hash).
    """
    private_key, public_key = generate_keypair()
    base_record = generate_provenance_record(
        actor_id="detector_worker_1",
        operation="INFERENCE_BATCH",
        inputs_hash="sha256_batch_images_root",
        outputs_hash="sha256_predicted_boxes",
        config_hash="sha256_runtime_config",
        private_key_pem=private_key,
        public_key_pem=public_key,
    )

    # Base record must verify cleanly
    assert verify_provenance_record(base_record) is True

    tested_fields = [
        "timestamp",
        "actor_id",
        "operation",
        "inputs_hash",
        "outputs_hash",
        "config_hash",
    ]
    tamper_results = {}

    for field in tested_fields:
        tampered_record = copy.deepcopy(base_record)
        tampered_record[field] = f"{tampered_record[field]}_tampered"
        passed = verify_provenance_record(tampered_record)
        # It must FAIL verification (passed == False)
        tamper_results[field] = {
            "tampered": True,
            "verification_passed": passed,
            "tamper_detected": not passed,
        }

    all_detected = all(res["tamper_detected"] for res in tamper_results.values())
    return {
        "fields_tested": len(tested_fields),
        "all_tampering_detected": all_detected,
        "tamper_break_rate": 1.0 if all_detected else 0.0,
        "field_details": tamper_results,
    }


def simulate_ledger_record_tampering(
    db_path: str | Path,
    record_count: int = 3,
    tampered_index: int = 2,
) -> dict[str, Any]:
    """Insert multiple records into Merkle ledger, tamper with record 2-of-3, and localize it.

    Verifies PPT claim:
    'Editing record 2-of-3 in the Merkle ledger is localised to that exact index,
     not just flagged generically.'
    """
    ledger = ProvenanceLedger(str(db_path))
    private_key, public_key = generate_keypair()

    created_ids = []
    for i in range(1, record_count + 1):
        rec = generate_provenance_record(
            actor_id=f"worker_{i}",
            operation="INFERENCE",
            inputs_hash=f"input_hash_{i}",
            outputs_hash=f"output_hash_{i}",
            config_hash="conf_v1",
            private_key_pem=private_key,
            public_key_pem=public_key,
        )
        entry_id = ledger.append_record(rec)
        created_ids.append(entry_id)

    # Verify initial valid state
    is_valid_initial, _ = ledger.verify_integrity()
    assert is_valid_initial is True

    # Attacker tampers directly with the SQLite database for record 2-of-3
    with sqlite3.connect(ledger.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT payload_json FROM ledger_entries WHERE id = ?", (tampered_index,))
        row = cursor.fetchone()
        payload = json.loads(row[0])
        payload["outputs_hash"] = "maliciously_flipped_bounding_box"
        cursor.execute(
            "UPDATE ledger_entries SET payload_json = ? WHERE id = ?",
            (json.dumps(payload), tampered_index),
        )
        conn.commit()

    # Re-verify ledger integrity
    is_valid_after, bad_indices = ledger.verify_integrity()

    return {
        "total_records": record_count,
        "tampered_index": tampered_index,
        "ledger_valid": is_valid_after,
        "corrupted_indices": bad_indices,
        "correctly_localized": (bad_indices == [tampered_index]),
    }
