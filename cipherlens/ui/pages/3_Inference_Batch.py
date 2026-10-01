import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

root_path = Path(__file__).resolve().parents[3]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.ui.shared import render_sidebar
from cipherlens.ingestion.inference_log_loader import load_inference_batch
from cipherlens.provenance.crypto import verify_provenance_record
from cipherlens.utils.finding import Finding

st.set_page_config(page_title="Inference Batch", page_icon="⚡", layout="wide")
render_sidebar()

st.title("Inference Batch Analysis")
st.markdown("Verify the cryptographic integrity of inference logs to detect post-scoring tampering.")

if not st.session_state.get("loaded_inference_batch"):
    st.warning("No inference batch loaded.")
    if st.button("Go back to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

batch_info = st.session_state.loaded_inference_batch

# Load the batch (cheap)
try:
    records, skipped = load_inference_batch(str(batch_info["path"]))
except Exception as e:
    st.error(f"Failed to load batch: {e}")
    st.stop()

# Auto-verify on load
if "batch_verification" not in st.session_state or st.button("Re-verify all", type="secondary"):
    results = []
    failed_count = 0
    for r in records:
        is_valid = verify_provenance_record(r)
        results.append({"record": r, "valid": is_valid})
        if not is_valid:
            failed_count += 1
    st.session_state.batch_verification = {"results": results, "failed": failed_count}

verif = st.session_state.batch_verification

# Summary bar
with st.container(border=True):
    verif_rate = ((len(records) - verif["failed"]) / len(records) * 100) if records else 100
    st.markdown(f"""
    **Batch:** `{batch_info['path'].name}`  
    **Records:** {len(records)}  
    **Skipped:** {skipped}  
    **Verification Rate:** {verif_rate:.1f}%
    """)

if verif["failed"] > 0:
    st.error(f"⚠️ {verif['failed']} record(s) failed signature verification — possible tampering detected.")
else:
    st.success("All records successfully verified against their cryptographic signatures.")

st.markdown("### Records")

# Render rows manually to allow expanders
for idx, res in enumerate(verif["results"]):
    r = res["record"]
    is_valid = res["valid"]
    
    icon = "✅" if is_valid else "❌"
    
    with st.expander(f"{icon} Record {r['record_id']} (Model: {r['model_id']}) - {r['timestamp']}"):
        st.json(r)
        
        if not is_valid:
            st.error("Signature verification failed for this record.")
            btn_key = f"quar_{r['record_id']}"
            
            # Allow creating a manual finding
            if st.button("Quarantine this record", key=btn_key):
                if "report_findings" not in st.session_state:
                    st.session_state.report_findings = []
                    
                finding = Finding(
                    category="PROVENANCE_TAMPERING",
                    severity="CRITICAL",
                    confidence=1.0,
                    reason=f"Signature verification failed for record {r['record_id']}",
                    affected_elements=[r["record_id"]],
                    evidence={"record": r}
                )
                
                st.session_state.report_findings.append(finding)
                
                if "report_document" in st.session_state:
                    del st.session_state.report_document
                st.toast(f"Quarantined record {r['record_id']}!", icon="🚨")

st.divider()

if st.button("Add findings to Assurance Report", type="primary"):
    # The findings are already added directly to the queue when clicking 'Quarantine',
    # but this button can just navigate to the report
    st.toast("Navigating to Assurance Report...", icon="✅")
    time.sleep(1)
    st.switch_page("pages/4_Assurance_Report.py")
