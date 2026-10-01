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
from cipherlens.governance.report_builder import build_report
from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.utils.finding import Finding

st.set_page_config(page_title="Assurance Report", page_icon="📜", layout="wide")
render_sidebar()

st.title("Assurance Report")

# Check if there is anything to report
if "report_findings" not in st.session_state and "last_report_id" not in st.session_state:
    st.info("You haven't run any analysis yet.")
    st.markdown("Start with [Dataset Analysis](1_Dataset_Analysis), [Model Analysis](2_Model_Analysis), or [Inference Batch](3_Inference_Batch).")
    st.stop()

# If a report ID exists from a previous run or the demo, fetch it from the ledger if not in session
if "last_report_id" in st.session_state and "report_document" not in st.session_state:
    # Try to load it directly
    if "report_findings" in st.session_state and "report_disposition" in st.session_state:
        # It's an in-memory draft/demo
        pass
    else:
        # Needs to be loaded from ledger (Phase 9/edge case)
        st.warning("Report exists but is not in current active memory buffer.")
        
# Build the draft report if not committed
if "report_document" not in st.session_state:
    findings = st.session_state.get("report_findings", [])
    
    # We need to build the report
    try:
        metadata = st.session_state.get("report_metadata", {})
        if "asset_type" not in metadata:
            metadata["asset_type"] = "DATASET"
        if "asset_identifier" not in metadata:
            metadata["asset_identifier"] = "unknown"
        if "asset_sha256" not in metadata:
            metadata["asset_sha256"] = "0" * 64

        report = build_report(
            findings=findings,
            asset_metadata=metadata,
            metrics_summary=st.session_state.get("report_metrics", {}),
            access_tier=st.session_state.get("loaded_model", {}).get("access_tier", "BLACK_BOX"),
            tamper_evident_audit_record={
                "merkle_root": "0" * 64,
                "signature": "dummy_sig",
                "signing_key_id": "dummy_key"
            }
        )
        st.session_state.report_document = report
    except Exception as e:
        st.error(f"Failed to build report: {e}")
        st.stop()

from cipherlens.governance.disposition import compute_risk_score

report = st.session_state.report_document
disposition = report["overall_disposition"]

# Calculate risk score dynamically since it's not part of the schema
findings_objs = [f if isinstance(f, Finding) else Finding(**f) for f in report['findings']]
risk_score = compute_risk_score(findings_objs)

# Render the Disposition Badge
st.markdown("### Final Disposition")
if disposition == "ACCEPT":
    st.success(f"## ✅ ACCEPT (Risk Score: {risk_score:.2f})")
elif disposition == "REVIEW":
    st.warning(f"## ⚠️ REVIEW (Risk Score: {risk_score:.2f})")
else:
    st.error(f"## 🚨 QUARANTINE (Risk Score: {risk_score:.2f})")

st.divider()

# Metrics Summary
st.markdown("### Metrics Summary")
m = report["metrics_summary"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Items Scanned", m.get("items_scanned", 0))
c2.metric("Critical Findings", m.get("critical_findings_count", 0))
c3.metric("High Findings", m.get("high_findings_count", 0))
c4.metric("Verification Rate", f"{m.get('signature_verification_rate', 1.0) * 100:.1f}%")

st.markdown("### Detailed Findings")
findings_list = report["findings"]
if findings_list:
    df = pd.DataFrame(findings_list)
    def severity_badge(s):
        return {"CRITICAL": "🔴 CRITICAL", "HIGH": "🟠 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW", "INFO": "⚪ INFO"}.get(s, s)
    df["severity_badge"] = df["severity"].apply(severity_badge)
    
    st.dataframe(
        df[["severity_badge", "category", "confidence", "reason", "finding_id"]],
        use_container_width=True,
        hide_index=True
    )
    
    selected = st.selectbox("View full evidence for finding", df["finding_id"])
    if selected:
        f_dict = df[df["finding_id"] == selected].iloc[0].to_dict()
        with st.expander("Raw Evidence JSON", expanded=True):
            st.json(f_dict.get("evidence", {}))
else:
    st.info("No findings recorded.")

st.divider()
st.markdown("### Actions")

report_json = json.dumps(report, indent=2)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        label="Download Report (.json)",
        data=report_json,
        file_name=f"assurance_report_{report['report_id']}.json",
        mime="application/json"
    )

with col2:
    if st.session_state.get("report_committed"):
        st.success("✅ Committed to Ledger")
    else:
        if st.button("Sign & commit to Ledger", type="primary"):
            with st.spinner("Signing and committing to Ledger..."):
                try:
                    ledger = ProvenanceLedger(db_path="reports/ledger.sqlite3")
                    
                    # Ensure the report has the tamper record populated if it wasn't already
                    if "tamper_evident_audit_record" not in report:
                         report["tamper_evident_audit_record"] = {
                             "merkle_root": "0"*64,
                             "signature": "dummy_sig",
                             "signing_key_id": "dummy_key"
                         }
                    
                    row_id = ledger.append_record(report)
                    tree = ledger.get_merkle_tree()
                    root_hash = tree.root or "0"*64
                    
                    st.session_state.report_committed = True
                    st.success(f"Report committed successfully! Merkle Root: `{root_hash[:16]}...`")
                    st.page_link("pages/5_Audit_Ledger.py", label="View Audit Ledger →")
                except Exception as e:
                    st.error(f"Failed to commit to ledger: {e}")
