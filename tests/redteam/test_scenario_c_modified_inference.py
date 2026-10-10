"""Red Team Scenario C: Modified Inference Log.

Validates:
1. Altering any field post-signing reliably breaks the Ed25519 signature, verified every time.
2. Editing record 2-of-3 in the Merkle ledger is localized to that exact index,
   not just flagged generically.
"""

import json
from pathlib import Path

from cipherlens.provenance.crypto import generate_keypair, generate_provenance_record
from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.redteam.tamper_inference import (
    simulate_field_tampering_attack,
    simulate_ledger_record_tampering,
)


def test_scenario_c_modified_inference(tmp_path: Path):
    """Red Team Scenario C: Modified Inference Log."""
    # 1. Test single-field alterations reliably breaking Ed25519 signature
    # Verifies PPT claim:
    # 'Altering one field after signing reliably breaks the Ed25519 signature, verified every time.'
    field_results = simulate_field_tampering_attack()
    assert field_results["all_tampering_detected"] is True
    assert field_results["tamper_break_rate"] == 1.0

    # 2. Test editing record 2-of-3 in the Merkle ledger is localized to that exact index
    # Verifies PPT claim:
    # 'Editing record 2-of-3 in the Merkle ledger is localised to that exact index, not just flagged generically.'
    db_path = tmp_path / "ledger_scenario_c.db"
    ledger_results = simulate_ledger_record_tampering(db_path, record_count=3, tampered_index=2)
    assert ledger_results["ledger_valid"] is False
    assert ledger_results["correctly_localized"] is True
    assert ledger_results["corrupted_indices"] == [2]

    # Save metrics for Coverage Statement
    results = {
        "scenario": "C",
        "ledger_valid": ledger_results["ledger_valid"],
        "corrupted_indices": ledger_results["corrupted_indices"],
        "correctly_localized": ledger_results["correctly_localized"],
        "field_tamper_detection_rate": field_results["tamper_break_rate"],
        "fields_tested": field_results["fields_tested"],
    }

    out_dir = Path("reports/redteam")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "scenario_c.json", "w") as f:
        json.dump(results, f, indent=2)
