import sys
import time
from pathlib import Path
import pandas as pd
import streamlit as st

root_path = Path(__file__).resolve().parents[3]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.ui.shared import render_sidebar
from cipherlens.data_integrity import analyze as analyze_data_integrity
from cipherlens.ingestion.coco_loader import load_coco_dataset
from cipherlens.ingestion.yolo_loader import load_yolo_dataset

st.set_page_config(page_title="Dataset Analysis", page_icon="📂", layout="wide")
render_sidebar()

st.title("Dataset Analysis")
st.markdown("Run spectral signatures, activation clustering, label consistency, and near-duplicate checks.")

if not st.session_state.get("loaded_dataset"):
    st.warning("No dataset loaded.")
    if st.button("Go back to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

dataset = st.session_state.loaded_dataset

# Summary bar
with st.container(border=True):
    st.markdown(f"""
    **Source:** `{dataset['path'].name}`  
    **Format:** `{dataset['format']}`  
    **Images:** `{dataset['images_dir'].name}`
    """)

if st.button("Run Data Integrity Analysis", type="primary"):
    # Clear old findings to show fresh state
    st.session_state.dataset_findings = None
    
    with st.spinner("Running Spectral Signatures..."):
        try:
            if dataset["format"] == "COCO":
                items, skipped = load_coco_dataset(str(dataset["path"]), str(dataset["images_dir"]))
            else:
                items, skipped = load_yolo_dataset(str(dataset["images_dir"]), str(dataset["path"]), ["0", "1", "2"])
        except Exception as e:
            st.error(f"Failed to load dataset: {e}")
            st.stop()
            
    with st.spinner("Running Activation Clustering... Checking near-duplicates... Aggregating contributor risk..."):
        try:
            findings = analyze_data_integrity(items, str(dataset["images_dir"]))
            st.session_state.dataset_findings = findings
            st.toast("Analysis complete!", icon="✅")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

if st.session_state.get("dataset_findings") is not None:
    findings = st.session_state.dataset_findings
    st.subheader(f"Findings ({len(findings)})")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Spectral Signature", "Label Consistency", "Near-Duplicates"])
    
    with tab1:
        st.markdown("### Finding Counts by Severity")
        if findings:
            df = pd.DataFrame([f.to_dict() for f in findings])
            
            def severity_badge(s):
                return {"CRITICAL": "🔴 CRITICAL", "HIGH": "🟠 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW", "INFO": "⚪ INFO"}.get(s, s)
                
            df["severity_badge"] = df["severity"].apply(severity_badge)
            
            # Simple bar chart of severity counts
            st.bar_chart(df["severity"].value_counts())
            
            st.markdown("### Contributor-level Risk")
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
            st.success("No anomalies detected across all dataset checks.")
            
    with tab2:
        spectral_findings = [f for f in findings if f.category == "DATA_POISONING" and "spectral" in f.reason.lower()]
        if spectral_findings:
            st.write(f"Found {len(spectral_findings)} spectral signature anomalies.")
            st.json([f.to_dict() for f in spectral_findings])
        else:
            st.success("No spectral anomalies flagged.")
            
    with tab3:
        label_findings = [f for f in findings if f.category == "LABEL_FLIP"]
        if label_findings:
            st.write(f"Found {len(label_findings)} label flips.")
            st.json([f.to_dict() for f in label_findings])
        else:
            st.success("No label flips flagged.")
            
    with tab4:
        dup_findings = [f for f in findings if f.category == "NEAR_DUPLICATE"]
        if dup_findings:
            st.write(f"Found {len(dup_findings)} near-duplicate clusters.")
            st.json([f.to_dict() for f in dup_findings])
        else:
            st.success("No near-duplicates flagged.")
            
    st.divider()
    if st.button("Add findings to Assurance Report", type="primary"):
        if "report_findings" not in st.session_state:
            st.session_state.report_findings = []
        st.session_state.report_findings.extend(findings)
        
        if "report_document" in st.session_state:
            del st.session_state.report_document
        
        st.session_state.report_metadata = {
            "asset_type": "DATASET",
            "asset_identifier": dataset["path"].name,
            "asset_sha256": "dataset_hash_placeholder",
            "format": dataset["format"],
        }
        
        st.toast("Added to Assurance Report queue!", icon="✅")
        time.sleep(1)
        st.switch_page("pages/4_Assurance_Report.py")
