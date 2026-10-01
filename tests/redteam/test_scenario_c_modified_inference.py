import json
from pathlib import Path

from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.provenance.crypto import generate_keypair, generate_provenance_record
from cipherlens.governance.report_builder import build_report

def test_scenario_c_modified_inference(tmp_path: Path):
    """Red Team Scenario C: Modified Inference Log.
    
    Simulates an attacker tampering with an inference log post-computation.
    The ledger verification must catch the invalid signature / altered content.
    """
    private_key, public_key = generate_keypair()
    ledger = ProvenanceLedger(str(tmp_path / "ledger.db"))
    
    # 1. Valid inference entry
    record = generate_provenance_record(
        actor_id="model_1",
        operation="INFERENCE",
        inputs_hash="fake_hash",
        outputs_hash="car",
        config_hash="cfg",
        private_key_pem=private_key,
        public_key_pem=public_key,
    )
    ledger.append_record(record)
    
    # 2. Tamper with the database directly (bypassing the append_entry signature)
    import sqlite3
    conn = sqlite3.connect(ledger.db_path)
    cursor = conn.cursor()
    # Attacker flips "car" to "truck"
    # We load the existing record, modify it, and overwrite payload_json
    cursor.execute("SELECT id, payload_json FROM ledger_entries LIMIT 1")
    row = cursor.fetchone()
    import json
    payload_json = json.loads(row[1])
    payload_json["outputs_hash"] = "truck" # Changed from "car"
    
    cursor.execute("UPDATE ledger_entries SET payload_json = ? WHERE id = ?", (json.dumps(payload_json), row[0]))
    conn.commit()
    conn.close()
    
    # 3. Verification should fail
    is_valid, bad_indices = ledger.verify_integrity()
    
    results = {
        "scenario": "C",
        "ledger_valid": is_valid,
        "corrupted_indices": bad_indices
    }
    
    out_dir = Path("reports/redteam")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "scenario_c.json", "w") as f:
        json.dump(results, f)
        
    assert is_valid is False
    assert len(bad_indices) > 0
