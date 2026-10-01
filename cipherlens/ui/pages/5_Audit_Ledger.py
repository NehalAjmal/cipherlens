import sys
import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

root_path = Path(__file__).resolve().parents[3]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.ui.shared import render_sidebar
from cipherlens.provenance.ledger import ProvenanceLedger

st.set_page_config(page_title="Audit Ledger", page_icon="🔗", layout="wide")
render_sidebar()

st.title("Audit Ledger")
st.markdown("Cryptographically verifiable, append-only Merkle ledger of all assurance activities.")

db_path = "reports/ledger.sqlite3"
ledger = ProvenanceLedger(db_path=db_path)

# 1. Load the ledger
try:
    entries = ledger.get_all_records()
except Exception as e:
    st.error(f"Failed to load ledger: {e}")
    st.stop()

if not entries:
    st.info("The ledger is currently empty. Run an analysis and commit a report to see it here.")
    st.stop()

# 2. Table of entries
st.markdown("### Ledger Entries")
df = pd.DataFrame([{
    "Seq Index": idx + 1,
    "Type": e.get("asset_metadata", {}).get("asset_type", "UNKNOWN"),
    "Payload": "Assurance Report",
    "Created At": e.get("evaluation_timestamp", "UNKNOWN")
} for idx, e in enumerate(entries)])

st.dataframe(df, hide_index=True, use_container_width=True)

st.divider()

# 3. Actions
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Verify")
    if st.button("Verify entire chain", type="primary"):
        with st.spinner("Recomputing Merkle root and validating signatures..."):
            try:
                is_valid, corrupted = ledger.verify_integrity()
                if is_valid:
                    st.success("✅ Valid. The Merkle chain is fully intact and untampered.")
                else:
                    st.error(f"❌ Broken: Corrupted records at IDs {corrupted}")
            except Exception as e:
                st.error(f"❌ Broken: {e}")

with col2:
    st.markdown("#### Anchoring")
    if st.button("Export Checkpoint"):
        checkpoint_path = f"reports/checkpoints/checkpoint_{int(time.time())}.json"
        Path("reports/checkpoints").mkdir(parents=True, exist_ok=True)
        try:
            # Reconstruct current chain state
            tree = ledger.get_merkle_tree()
            state = {
                "latest_merkle_root": tree.root,
                "record_count": len(entries),
                "timestamp": int(time.time())
            }
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            st.success(f"Checkpoint exported to `{checkpoint_path}`")
            st.info("Copy this file to a second device or medium to complete the external-anchoring guarantee.")
        except Exception as e:
            st.error(f"Failed to export checkpoint: {e}")

with col3:
    st.markdown("#### Demo Tools")
    with st.container(border=True):
        st.markdown("<span style='color: #C00000; font-weight: bold;'>Danger Zone</span>", unsafe_allow_html=True)
        if st.button("🔧 Simulate tampering (demo only)", help="Directly alters the SQLite payload of the last entry."):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # Tamper with the last entry's payload_json
                cursor.execute("SELECT payload_json FROM ledger_entries ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    bad_payload = row[0].replace('"overall_disposition": "QUARANTINE"', '"overall_disposition": "ACCEPT"')
                    bad_payload = bad_payload.replace('"overall_disposition": "REVIEW"', '"overall_disposition": "ACCEPT"')
                    # Just mangle it slightly if it didn't have those
                    bad_payload = bad_payload.replace("}", ',"tampered":true}')
                    
                    cursor.execute("UPDATE ledger_entries SET payload_json = ? WHERE id = (SELECT MAX(id) FROM ledger_entries)", (bad_payload,))
                    conn.commit()
                    st.toast("Tampering applied to disk! Click 'Verify entire chain' to catch it.", icon="🚨")
                conn.close()
            except Exception as e:
                st.error(f"Demo tampering failed: {e}")
                
        if st.button("Restore demo ledger"):
            import shutil
            backup_path = "data/samples/demo_ledger_backup.sqlite3"
            if Path(backup_path).exists():
                shutil.copy(backup_path, db_path)
                st.toast("Ledger restored from demo backup.", icon="✅")
            else:
                if Path(db_path).exists():
                    Path(db_path).unlink()
                st.toast("Ledger reset (backup not found).", icon="✅")
            time.sleep(1)
            st.rerun()
