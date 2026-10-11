import hashlib
from pathlib import Path
import streamlit as st
from cipherlens.config import get_config

def render_sidebar():
    """Renders the common sidebar elements across all pages."""
    with st.sidebar:
        # Title and static badge
        st.title("CipherLens 🔍")
        st.caption("🔒 **100% Offline • Air-Gapped CV Assurance**")
        st.divider()

        st.markdown("### Current Session")
        
        # Dataset status
        dataset = st.session_state.get("loaded_dataset")
        if dataset:
            st.success(f"📂 Dataset: {dataset['path'].name}")
        else:
            st.info("📂 Dataset: None")
            
        # Model status
        model = st.session_state.get("loaded_model")
        if model:
            tier_badge = "🟢" if model.get('access_tier') == 'WHITE_BOX' else "🟠"
            st.success(f"🧠 Model: {model['path'].name}")
            st.caption(f"Tier: {tier_badge} {model.get('access_tier', 'UNKNOWN')}")
        else:
            st.info("🧠 Model: None")
            
        # Inference Batch status
        batch = st.session_state.get("loaded_inference_batch")
        if batch:
            st.success(f"⚡ Batch: {batch['path'].name}")
        else:
            st.info("⚡ Batch: None")

        if st.button("Clear session", type="secondary"):
            st.session_state.clear()
            st.rerun()

        st.divider()
        
        # Config hash indicator
        root_path = Path(__file__).resolve().parents[2]
        config_path = Path("configs/default.yaml")
        if not config_path.exists():
            config_path = root_path / "configs" / "default.yaml"
        if config_path.exists():
            with open(config_path, "rb") as f:
                config_hash = hashlib.sha256(f.read()).hexdigest()[:8]
            
            with st.expander(f"⚙️ Config (Hash: {config_hash})"):
                st.caption("Active `configs/default.yaml` (read-only)")
                config = get_config()
                st.json(config.model_dump())
