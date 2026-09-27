# CipherLens

**An offline, air-gapped computer-vision integrity assurance tool.**

CipherLens cryptographically and statistically proves whether the training data, model weights, and inference outputs in a multi-contributor computer-vision pipeline can be trusted — without requiring retraining or full white-box access.

Built for Smart India Hackathon (problem statement SIH26228).

---

## Quick Start

### 1. Setup

```bash
# macOS / Linux
bash scripts/setup_env.sh
source .venv/bin/activate

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
. .venv\Scripts\Activate.ps1
```

### 2. Verify

```bash
python -c "import cipherlens; print('CipherLens OK')"
pytest
```

### 3. Run the Dashboard

```bash
streamlit run cipherlens/ui/streamlit_app.py
```

---

## Documentation

See `docs/` for full documentation:

- **PRD.md** — Product requirements
- **ARCHITECTURE.md** — Repository structure and module boundaries
- **PLAN.md** — Build roadmap (phases 0–11)
- **BACKEND_SCHEMA.md** — Data shapes and JSON schemas
- **APP_FLOW.md** — UI page flow and states
- **TRD.md** — Technical requirements and dependency audit
- **AI_RULES.md** — Non-negotiable engineering rules

---

## Key Features

- **Training-Data Integrity** — Spectral Signatures + Activation Clustering backdoor detection, label-flip detection, near-duplicate detection, contributor risk scoring
- **Model Integrity** — Neural Cleanse (white-box) + STRIP (black-box) backdoor detection with explicit access-tier reporting
- **Inference Provenance** — SHA-256 + Ed25519 signed provenance records with tamper detection
- **Distribution Shift** — MMD + KS test + Energy-OOD scoring
- **Governance** — Schema-validated Assurance Reports, weighted-sum disposition, Merkle-chained audit ledger

---

## License

See repository root for license information.
