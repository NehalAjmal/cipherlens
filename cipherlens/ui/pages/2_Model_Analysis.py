import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

root_path = Path(__file__).resolve().parents[3]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.ui.shared import render_sidebar
from cipherlens.model_integrity import analyze as analyze_model_integrity
from cipherlens.ingestion.model_loader import load_model

st.set_page_config(page_title="Model Analysis", page_icon="🧠", layout="wide")
render_sidebar()

st.title("Model Analysis")
st.markdown("Run Neural Cleanse, STRIP, and weight parameter checks.")

if not st.session_state.get("loaded_model"):
    st.warning("No model loaded.")
    if st.button("Go back to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

model_info = st.session_state.loaded_model

# Load model logic to get the manifest hash (if not already cached)
try:
    model_handle = load_model(str(model_info["path"]), model_info["path"].name, access_tier_available=model_info["access_tier"])
except Exception as e:
    st.error(f"Failed to verify model for analysis: {e}")
    st.stop()

# Summary bar
with st.container(border=True):
    tier_badge = "🟢" if model_info['access_tier'] == 'WHITE_BOX' else "🟠"
    st.markdown(f"""
    **Model:** `{model_info['path'].name}`  
    **Format:** `{model_info['format']}`  
    **SHA-256:** `{model_handle.manifest.sha256[:12]}...` (truncated)  
    **Access Tier:** {tier_badge} `{model_info['access_tier']}`
    """)

# Degraded state banner
if model_info["access_tier"] == "BLACK_BOX":
    st.warning("Some checks are unavailable without white-box access. This assessment's confidence is bounded — see the report's `access_tier` field.")

if st.button("Run Model Integrity Analysis", type="primary"):
    st.session_state.model_findings = None
    
    with st.spinner(f"Running {model_info['access_tier']} battery..."):
        try:
            findings = analyze_model_integrity(model_handle)
            st.session_state.model_findings = findings
            st.toast("Model analysis complete!", icon="✅")
        except Exception as e:
            st.error(f"Model analysis failed: {e}")
            st.stop()

if st.session_state.get("model_findings") is not None:
    findings = st.session_state.model_findings
    st.subheader(f"Findings ({len(findings)})")
    
    tab1, tab2, tab3 = st.tabs(["Neural Cleanse", "STRIP", "Weight Checks"])
    
    with tab1:
        st.markdown("### Neural Cleanse (White-Box Only)")
        if model_info["access_tier"] == "BLACK_BOX":
            st.info("Unavailable — black-box access only.")
        else:
            nc_findings = [f for f in findings if f.category == "MODEL_BACKDOOR" and "Neural Cleanse" in f.reason]
            if nc_findings:
                st.write(f"Found {len(nc_findings)} trigger signatures.")
                for f in nc_findings:
                    with st.expander("Trigger Evidence"):
                        st.json(f.to_dict())
            else:
                st.success("No high-confidence triggers found via Neural Cleanse.")
                
    with tab2:
        st.markdown("### STRIP Perturbation Battery")
        strip_findings = [f for f in findings if f.category == "MODEL_BACKDOOR" and "STRIP" in f.reason]
        if strip_findings:
            st.write(f"Found {len(strip_findings)} backdoored inputs via STRIP.")
            for f in strip_findings:
                with st.expander("STRIP Evidence"):
                    st.json(f.to_dict())
        else:
            st.success("No anomalously low-entropy inputs detected via STRIP.")
            
    with tab3:
        st.markdown("### Weight Checks")
        if model_info["access_tier"] == "BLACK_BOX":
            st.info("Unavailable — black-box access only.")
        else:
            weight_findings = [f for f in findings if f.category == "MODEL_BACKDOOR" and ("spectral" in f.reason.lower() or "kurtosis" in f.reason.lower())]
            if weight_findings:
                st.write(f"Found {len(weight_findings)} anomalous layer behaviors.")
                for f in weight_findings:
                    with st.expander("Layer Evidence"):
                        st.json(f.to_dict())
            else:
                st.success("No suspicious weight kurtosis or spectral norms detected.")
                
    st.divider()
    if st.button("Add findings to Assurance Report", type="primary"):
        if "report_findings" not in st.session_state:
            st.session_state.report_findings = []
        st.session_state.report_findings.extend(findings)
        
        if "report_document" in st.session_state:
            del st.session_state.report_document
        
        # Override metadata with the model since it was just run
        st.session_state.report_metadata = {
            "asset_type": "MODEL",
            "asset_identifier": model_handle.manifest.model_id,
            "asset_sha256": model_handle.manifest.sha256,
            "format": model_info["format"]
        }
        
        st.toast("Added to Assurance Report queue!", icon="✅")
        time.sleep(1)
        st.switch_page("pages/4_Assurance_Report.py")
