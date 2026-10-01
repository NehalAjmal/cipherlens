"""Append-only SQLite ledger for provenance records.

Implements BACKEND_SCHEMA.md §5. Maintains a Merkle tree of all
committed provenance records. Ensures append-only guarantees.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

from cipherlens.provenance.crypto import canonicalize
from cipherlens.provenance.merkle import MerkleTree
from cipherlens.utils.hashing import sha256_digest


class ProvenanceLedger:
    """SQLite-backed append-only ledger for provenance records."""
    
    def __init__(self, db_path: str | Path):
        """Initialize the ledger, creating the schema if it doesn't exist.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._init_db()
        
    def _init_db(self):
        """Create the table if it does not exist.
        
        Matches the schema in BACKEND_SCHEMA.md §5 exactly.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            # We strictly avoid UPDATE or DELETE in this module.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            
    def append_record(self, record: dict[str, Any]) -> int:
        """Append a provenance record to the ledger.
        
        Args:
            record: The signed provenance record dictionary.
            
        Returns:
            The row ID of the inserted record.
        """
        payload_json = canonicalize(record)
        payload_hash = sha256_digest(payload_json.encode("utf-8"))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO ledger_entries (payload_hash, payload_json)
                VALUES (?, ?)
                """,
                (payload_hash, payload_json)
            )
            conn.commit()
            return cursor.lastrowid
            
    def get_all_records(self) -> list[dict[str, Any]]:
        """Retrieve all records from the ledger in insertion order."""
        records = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT payload_json FROM ledger_entries ORDER BY id ASC")
            for row in cursor:
                records.append(json.loads(row["payload_json"]))
        return records
        
    def get_merkle_tree(self) -> MerkleTree:
        """Recompute and return the full Merkle tree of the current ledger.
        
        The leaves are the payload_hashes in insertion order.
        """
        leaf_hashes = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT payload_hash FROM ledger_entries ORDER BY id ASC")
            for row in cursor:
                leaf_hashes.append(row[0])
                
        return MerkleTree(leaf_hashes)

    def verify_integrity(self) -> tuple[bool, list[int]]:
        """Verify the cryptographic integrity of the ledger.
        
        Checks that every stored payload_json matches its stored payload_hash.
        Returns a tuple of (is_valid, list_of_corrupted_ids).
        """
        corrupted_ids = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, payload_hash, payload_json FROM ledger_entries ORDER BY id ASC")
            for row in cursor:
                computed_hash = sha256_digest(row["payload_json"].encode("utf-8"))
                if computed_hash != row["payload_hash"]:
                    corrupted_ids.append(row["id"])
                    
        return len(corrupted_ids) == 0, corrupted_ids

    def export_checkpoint(self, export_path: str | Path) -> str:
        """Export a checkpoint per BACKEND_SCHEMA.md §5.1.
        
        Args:
            export_path: Where to save the checkpoint JSON file.
            
        Returns:
            The root hash of the tree at the time of checkpoint.
        """
        tree = self.get_merkle_tree()
        root_hash = tree.root or ""
        
        records = self.get_all_records()
        
        checkpoint = {
            "merkle_root": root_hash,
            "record_count": len(records),
            "records": records
        }
        
        export_path = Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(canonicalize(checkpoint))
            
        return root_hash
