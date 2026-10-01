"""Unit tests for the provenance ledger.

Verifies append-only behavior, Merkle tree integration, and checkpoint export.
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from cipherlens.provenance.crypto import canonicalize
from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.utils.hashing import sha256_digest


@pytest.fixture
def temp_db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_ledger.sqlite3"


@pytest.fixture
def ledger(temp_db_path):
    return ProvenanceLedger(temp_db_path)


def test_append_and_retrieve_records(ledger):
    """Verify records can be appended and retrieved in order."""
    record1 = {"foo": "bar"}
    record2 = {"baz": 123}
    
    id1 = ledger.append_record(record1)
    id2 = ledger.append_record(record2)
    
    assert id1 == 1
    assert id2 == 2
    
    records = ledger.get_all_records()
    assert len(records) == 2
    assert records[0] == record1
    assert records[1] == record2


def test_merkle_tree_integration(ledger):
    """Verify the ledger correctly builds a Merkle tree from its records."""
    records = [{"val": i} for i in range(3)]
    for r in records:
        ledger.append_record(r)
        
    tree = ledger.get_merkle_tree()
    assert len(tree.leaves) == 3
    
    # Check that leaves match the hashes of canonicalized records
    expected_leaves = [
        sha256_digest(canonicalize(r).encode("utf-8")) for r in records
    ]
    assert tree.leaves == expected_leaves


def test_ledger_detects_tampering(ledger):
    """Verify that verify_integrity catches out-of-band DB modification.
    
    The code has no UPDATE/DELETE methods, so we simulate an attacker
    modifying the SQLite file directly.
    """
    record1 = {"foo": "bar"}
    record2 = {"foo": "baz"}
    
    ledger.append_record(record1)
    ledger.append_record(record2)
    
    is_valid, corrupted = ledger.verify_integrity()
    assert is_valid is True
    assert len(corrupted) == 0
    
    # Simulate attacker tampering with row 2's payload JSON directly
    with sqlite3.connect(ledger.db_path) as conn:
        conn.execute(
            "UPDATE ledger_entries SET payload_json = ? WHERE id = 2",
            ('{"foo": "evil"}',)
        )
        conn.commit()
        
    is_valid, corrupted = ledger.verify_integrity()
    assert is_valid is False
    assert corrupted == [2]


def test_checkpoint_export(ledger, temp_db_path):
    """Verify checkpoint export produces a valid JSON file with correct root."""
    records = [{"val": i} for i in range(5)]
    for r in records:
        ledger.append_record(r)
        
    tree = ledger.get_merkle_tree()
    expected_root = tree.root
    
    export_path = temp_db_path.parent / "checkpoint.json"
    actual_root = ledger.export_checkpoint(export_path)
    
    assert actual_root == expected_root
    assert export_path.exists()
    
    with open(export_path, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)
        
    assert checkpoint_data["merkle_root"] == expected_root
    assert checkpoint_data["record_count"] == 5
    assert len(checkpoint_data["records"]) == 5
    assert checkpoint_data["records"][0] == records[0]
