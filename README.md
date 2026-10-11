<div align="center">

# 🛡️ CIPHERLENS
### Trustworthy Computer Vision Integrity Assurance in Multi-Contributor Pipelines
**Smart India Hackathon 2026** · *Problem Statement: SIH26228* · *Theme: Blockchain & Cybersecurity*
<p align="center">
  <a href="https://cipherlens.streamlit.app"><img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Streamlit App" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/Runtime-100%25%20Air--Gapped-0E7090?style=for-the-badge&logo=shield&logoColor=white" alt="Air-Gapped" /></a>
  <a href="docs/BACKEND_SCHEMA.md"><img src="https://img.shields.io/badge/Crypto-Ed25519%20%2B%20Merkle-10B981?style=for-the-badge&logo=lock&logoColor=white" alt="Ed25519" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/ML%20Engines-PyTorch%20%7C%20ONNX-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch/ONNX" /></a>
  <a href="test_results.txt"><img src="https://img.shields.io/badge/Tests-46%20Passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest" /></a>
</p>

> **"Nothing ties data, model, and runtime inference together with cryptographic proof — CipherLens closes that gap end-to-end with zero cloud dependencies and zero retraining."**

</div>

<br/>

| Team Information | Submission Metadata | Operational Guarantees |
|:---|:---|:---|
| **Team Name:** Shadow Cipher | **Problem Statement:** SIH26228 (Software) | **Network Calls:** Exactly 0 on critical path |
| **Team ID:** 168268 | **Theme:** Blockchain & Cybersecurity | **Retraining Required:** Zero (Post-hoc baseline) |
| **Repository:** [NehalAjmal/cipherlens](https://github.com/NehalAjmal/cipherlens) | **Access Tier Honesty:** Explicit White/Black Box | **Hardware:** Standard CPU (No GPU required) |

---


## 1. Where Trust Breaks Down in the Pipeline

| Pipeline Stage | Vulnerability & Attack Surface | Risk Addressed | CipherLens Solution |
|---|---|---|---|
| **1. Data Intake** | COCO / YOLO batches pooled from untrusted outside contributors | Poisoning, label flips, backdoor triggers, flooding | **Spectral Signatures + Activation Clustering**, k-NN label-entropy consistency, perceptual hash dedup |
| **2. Pretrained / Vendor Models** | PyTorch / ONNX weights arrive with no record of provenance | Silent substitution, trojans baked into weights, unsafe deserialization | **Neural Cleanse (white-box) + STRIP (black-box)**, safe deserialization via `safe_torch_load()` |
| **3. Inference in Production** | Bounding box outputs sent downstream without transit verification | Replay attacks, out-of-band tampering, broken chain of custody | **SHA-256 + Ed25519 signing + append-only Merkle ledger** |

---

## 2. Technical Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               MULTI-CONTRIBUTOR INTAKE                 │
                    │   COCO / YOLO Datasets  │  PyTorch / ONNX  │  JSONL    │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
                     Ingestion Layer: Unified Schema (zero-copy via PyArrow)
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
      [Data Integrity]                 [Model Integrity]             [Distribution Shift]
  • Spectral Signatures            • Neural Cleanse (white-box)     • MMD (multi-scale RBF)
  • Activation Clustering          • STRIP battery (black-box)      • 2-sample KS test
  • k-NN Label Consistency         • Weight spectral norm / kurt.   • Energy-OOD scoring
  • Perceptual Hash Dedup          • Access-tier honesty tag        • Separates benign vs adv.
                 │                              │                              │
                 └──────────────────────────────┼──────────────────────────────┘
                                                │
                                                ▼
                         Inference Provenance: SHA-256 + Ed25519 Signing
                                                │
                                                ▼
                    Governance & Weighted Risk Fusion (Accept / Review / Quarantine)
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     Merkle-Chained Audit Ledger                                  Offline Streamlit Dashboard
     (Append-only, tamper-evident)                                (Interactive analyst UI)
```

---

## 3. Empirical Test Results (Reproduced in Repo)

Every metric in the table below is directly computed from executed test runs in this repository:

| Capability / Benchmark | Target / PPT Claim | Test Suite Result | Verification File |
|---|:---:|:---:|---|
| **Poisoned Data Recall** (Spectral Signatures + Activation Clustering) | **100% recall** | **100.0%** (0 false alarms) | [`tests/redteam/test_scenario_a_poisoned_data.py`](tests/redteam/test_scenario_a_poisoned_data.py) |
| **White-Box Backdoor Detection** (Neural Cleanse, ~500 steps) | **100% detection** | **100.0% real detections**, 0 false alarms | [`tests/redteam/test_scenario_b_trojaned_model.py`](tests/redteam/test_scenario_b_trojaned_model.py) |
| **Black-Box Backdoor Detection** (STRIP perturbation battery) | **1-in-20 FPR** | **100.0% recall, 5.0% (1-in-20) FPR** | [`tests/redteam/test_scenario_b_trojaned_model.py`](tests/redteam/test_scenario_b_trojaned_model.py) |
| **Provenance Tamper Proofing** (Ed25519 signature) | **100% break rate** | **100.0% detection** across all fields | [`tests/redteam/test_scenario_c_modified_inference.py`](tests/redteam/test_scenario_c_modified_inference.py) |
| **Merkle Ledger Localization** | **Localize record 2-of-3** | **Index `[2]` specifically localized** | [`tests/unit/provenance/test_ledger.py`](tests/unit/provenance/test_ledger.py) |
| **Energy-OOD Signal Separation** | **48-point gap** | **100% Adv. vs 52% Benign (48.0 pt gap)** | [`tests/unit/distribution_shift/test_energy_ood.py`](tests/unit/distribution_shift/test_energy_ood.py) |
| **Critical Findings Fixed vs Open** | **2 fixed, 6 open** | **2 fixed & verified, 6 tracked openly** | [`docs/VALIDATION_TRAIL.md`](docs/VALIDATION_TRAIL.md) |
| **Network Calls on Critical Path** | **0 network calls** | **0 outbound calls** | Enforced by security invariant |

---

## 4. Quick Start

### 1. Environment Setup

CipherLens runs on Python 3.11 with zero external cloud dependencies.

```bash
# Clone the repository
git clone https://github.com/NehalAjmal/cipherlens.git
cd cipherlens

# Setup virtual environment and dependencies
bash scripts/setup_env.sh
source .venv/bin/activate
```

*For Windows (PowerShell):*
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
. .venv\Scripts\Activate.ps1
```

### 2. Run Test Suite

Verify all 46 unit, integration, and red-team tests:

```bash
pytest
```

Output: `46 passed, 1 skipped (optional Docker container containment test), 0 failures`

### 3. Run Headless Demo Pipeline

Execute the end-to-end assurance pipeline headlessly:

```bash
python scripts/run_demo.py
```

This ingests sample datasets and models, computes data/model integrity metrics, generates a signed and validated Assurance Report, and commits the result to the local Merkle ledger (`reports/ledger.sqlite3`).

### 4. Launch Offline Streamlit UI

```bash
streamlit run cipherlens/ui/streamlit_app.py
```

The interactive dashboard opens in your browser at `http://localhost:8501`:
* **Dataset Analysis:** Spectral signatures, activation clustering, label consistency, and duplicate detection.
* **Model Analysis:** Neural Cleanse trigger inspection, STRIP entropy battery, and weight spectral norm ratios.
* **Inference Batch:** Provenance verification of predicted bounding boxes and cryptographic signatures.
* **Assurance Report:** Schema-validated JSON report with weighted-sum risk scores and 3-tier disposition.
* **Audit Ledger:** Append-only Merkle ledger inspection, tamper simulation, and checkpoint export.

### 5. Deploy as Live Website (Streamlit Community Cloud)

CipherLens is pre-configured for one-click hosting on **[Streamlit Community Cloud](https://share.streamlit.io)** with zero cloud costs or external API keys:

1. Push this repository to GitHub: `https://github.com/NehalAjmal/cipherlens`
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
3. Click **"New app"** and specify the deployment configuration:
   * **Repository:** `NehalAjmal/cipherlens`
   * **Branch:** `main`
   * **Main file path:** `cipherlens/ui/streamlit_app.py`
   * **App URL:** `cipherlens.streamlit.app` *(or custom subdomain)*
4. Click **Deploy!**

> **Air-Gapped Cloud Invariant:** The repository already contains `packages.txt` for Debian graphics runtime libraries (`libgl1`, `libglib2.0-0`), pre-cached backbone weights (`models_cache/backbone/resnet18.pt`), and self-healing SQLite demo ledgers. No external network requests are made during runtime assurance checks.

---

## 5. Security Invariants

1. **Zero Outbound Network Calls:** Every computation runs 100% locally on CPU or local GPU; no telemetry, cloud APIs, or hosted LLM endpoints are called at runtime.
2. **Safe Deserialization (`safe_torch_load`):** Arbitrary code execution via pickle deserialization is strictly prevented by enforcing `weights_only=True` across all 7 PyTorch model loading sites.
3. **Canonical Cryptography:** Canonical JSON formatting follows RFC 8785 principles (`sort_keys=True`, `separators=(',', ':')`) for deterministic SHA-256 digests and Ed25519 signing.
4. **Weighted-Sum Disposition:** System dispositions (`ACCEPT` / `REVIEW` / `QUARANTINE`) use continuous severity weights ($W_{INFO}=0, W_{LOW}=1, W_{MED}=3, W_{HIGH}=7, W_{CRIT}=15$) rather than easily evadable boolean AND/OR gates.
5. **Append-Only Merkle Audit Ledger:** Ledger operations only permit `INSERT` statements; any out-of-band byte or database modifications immediately invalidate the root hash and localize the exact corrupted index.

---

## 6. Complete Documentation

Detailed specifications and architectural contracts are available in the [`docs/`](docs/) directory:

* [`docs/PRD.md`](docs/PRD.md) — Product Requirements Document (in-scope vs out-of-scope contracts)
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Module boundaries, import rules, and layout contract
* [`docs/COVERAGE_STATEMENT.md`](docs/COVERAGE_STATEMENT.md) — Empirical attack coverage statement
* [`docs/VALIDATION_TRAIL.md`](docs/VALIDATION_TRAIL.md) — Full log of 15 code-review findings (8 critical, 7 architectural)
* [`docs/BACKEND_SCHEMA.md`](docs/BACKEND_SCHEMA.md) — Complete JSON schemas and ledger specifications
* [`docs/APP_FLOW.md`](docs/APP_FLOW.md) — Streamlit UI states, pages, and interactive flows
* [`docs/TRD.md`](docs/TRD.md) — Technical requirements, hardware baseline, and zero-cost dependency audit

---

## 7. License

Distributed under the Apache 2.0 / MIT Open Source License. All dependencies are free and open-source.
