import sys
import time
from pathlib import Path
import streamlit as st

# Add project root to sys.path so 'cipherlens' is resolvable when run directly
root_path = Path(__file__).resolve().parents[2]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.ui.shared import render_sidebar
from cipherlens.ingestion.model_loader import load_model

st.set_page_config(
    page_title="CipherLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

# Header
st.title("CipherLens — Trustworthy CV Integrity Assurance")
st.markdown("Detect data poisoning, label flips, model backdoors, and distribution drift entirely offline.")
st.divider()

def resolve_path(p: str | Path) -> Path:
    path = Path(p)
    if path.exists():
        return path
    candidate = root_path / p
    if candidate.exists():
        return candidate
    return path

col1, col2, col3 = st.columns(3)

# 1. Analyze a Dataset
with col1:
    with st.container(border=True):
        st.subheader("Analyze a Dataset")
        ds_path = st.text_input("Dataset File/Folder", value="data/samples/annotations/instances_samples.json", key="ds_path")
        img_dir = st.text_input("Images Directory", value="data/samples/images", key="img_dir")
        ds_format = st.selectbox("Format", ["COCO", "YOLO"], key="ds_format")
        
        if st.button("Load Dataset", type="primary"):
            p_ds = resolve_path(ds_path)
            p_img = resolve_path(img_dir)
            if p_ds.exists() and p_img.exists():
                st.session_state.loaded_dataset = {
                    "path": p_ds,
                    "images_dir": p_img,
                    "format": ds_format
                }
                st.toast("Dataset loaded successfully!", icon="✅")
            else:
                st.error("Invalid paths provided. Please check the dataset and images directories.")
                
        if st.session_state.get("loaded_dataset"):
            st.page_link("pages/1_Dataset_Analysis.py", label="Go to Dataset Analysis →")

# 2. Analyze a Model
with col2:
    with st.container(border=True):
        st.subheader("Analyze a Model")
        mdl_path = st.text_input("Model File (.pt, .pth, .onnx)", value="data/samples/resnet50_clean.onnx", key="mdl_path")
        sim_blackbox = st.toggle("Simulate black-box access only", key="sim_blackbox")
        
        if st.button("Load Model", type="primary"):
            p_mdl = resolve_path(mdl_path)
            if mdl_path and p_mdl.exists():
                ext = p_mdl.suffix.lower()
                mdl_format = "PYTORCH" if ext in {".pt", ".pth"} else "ONNX"
                tier_available = "BLACK_BOX" if (mdl_format == "ONNX" or sim_blackbox) else "WHITE_BOX"
                
                with st.spinner("Loading model to detect format..."):
                    try:
                        # Dry run load to confirm it's readable
                        load_model(str(p_mdl), p_mdl.name, access_tier_available=tier_available)
                        st.session_state.loaded_model = {
                            "path": p_mdl,
                            "format": mdl_format,
                            "access_tier": tier_available
                        }
                        st.toast("Model loaded successfully!", icon="✅")
                    except Exception as e:
                        st.error(f"Failed to load model: {e}")
            else:
                st.error("Invalid model path.")
                
        if st.session_state.get("loaded_model"):
            st.page_link("pages/2_Model_Analysis.py", label="Go to Model Analysis →")

# 3. Check an Inference Batch
with col3:
    with st.container(border=True):
        st.subheader("Check an Inference Batch")
        batch_path = st.text_input("Batch File (JSONL)", value="data/samples/sample_inference_batch.jsonl", key="batch_path")
        
        if st.button("Load Batch", type="primary"):
            p_batch = resolve_path(batch_path)
            if batch_path and p_batch.exists():
                st.session_state.loaded_inference_batch = {
                    "path": p_batch
                }
                st.toast("Batch loaded successfully!", icon="✅")
            else:
                st.error("Invalid inference batch path.")
                
        if st.session_state.get("loaded_inference_batch"):
            st.page_link("pages/3_Inference_Batch.py", label="Go to Inference Batch →")

st.divider()

# Run Full Demo
st.markdown("### Quick Start")
if st.button("Run Full Demo"):
    with st.spinner("Running end-to-end pipeline on sample dataset..."):
        from cipherlens.pipeline import run_pipeline
        try:
            p_demo_ds = resolve_path("data/samples/annotations/instances_samples.json")
            p_demo_img = resolve_path("data/samples/images")
            p_demo_mdl = resolve_path("data/samples/resnet50_clean.onnx")
            report = run_pipeline(
                dataset_path=str(p_demo_ds),
                images_dir=str(p_demo_img),
                dataset_format="COCO",
                model_path=str(p_demo_mdl),
                model_format="ONNX"
            )
            st.session_state.last_report_id = report["report_id"]
            st.session_state.report_document = report
            
            # Put the report findings in session state so Assurance Report page can display it
            st.session_state.report_findings = report.get("findings", [])
            st.session_state.report_metrics = report.get("metrics_summary", {})
            st.session_state.report_metadata = report.get("asset_metadata", {})
            st.session_state.report_disposition = report.get("overall_disposition", "UNKNOWN")
            st.session_state.report_risk_score = report.get("risk_score", 0.0)
            
            st.success("Demo complete! Redirecting to Assurance Report...")
            time.sleep(1)
            st.switch_page("pages/4_Assurance_Report.py")
        except Exception as e:
            st.error(f"Demo failed: {e}")

st.markdown("---")
# Coverage Statement Expander
with st.expander("Coverage Statement (What this tool does and does not detect)"):
    cov_path = root_path / "docs" / "COVERAGE_STATEMENT.md"
    if cov_path.exists():
        with open(cov_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.write("COVERAGE_STATEMENT.md not found.")
