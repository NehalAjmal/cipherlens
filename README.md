<div align="center">

# CIPHERLENS
### Trustworthy Computer Vision Integrity Assurance in Multi-Contributor Pipelines
**Smart India Hackathon 2026** | *Problem Statement: SIH26228* | *Theme: Blockchain & Cybersecurity*

<p align="center">
  <a href="https://cipherlens.streamlit.app"><img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Streamlit App" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/Runtime-100%25%20Air--Gapped-0E7090?style=for-the-badge&logo=shield&logoColor=white" alt="Air-Gapped" /></a>
  <a href="docs/BACKEND_SCHEMA.md"><img src="https://img.shields.io/badge/Crypto-Ed25519%20%2B%20Merkle-10B981?style=for-the-badge&logo=lock&logoColor=white" alt="Ed25519" /></a>
  <a href="docs/TRD.md"><img src="https://img.shields.io/badge/ML%20Engines-PyTorch%20%7C%20ONNX-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch/ONNX" /></a>
  <a href="test_results.txt"><img src="https://img.shields.io/badge/Tests-46%20Passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest" /></a>
</p>

> **"Nothing ties data, model, and runtime inference together with cryptographic proof: CipherLens closes that gap end-to-end with zero cloud dependencies and zero retraining."**

</div>

<br/>

| Team Information | Submission Metadata | Operational Guarantees |
|:---|:---|:---|
| **Team Name:** Shadow Cipher | **Problem Statement ID:** SIH26228 | **Network Calls:** Exactly 0 on critical path |
| **Team ID:** 168268 | **PS Category:** Software | **Retraining Required:** Zero (Post-hoc baseline) |
| **Theme:** Blockchain & Cybersecurity | **Repository:** [NehalAjmal/cipherlens](https://github.com/NehalAjmal/cipherlens) | **Access Tier Honesty:** Explicit White/Black Box |
| **Live App:** [cipherlens.streamlit.app](https://cipherlens.streamlit.app) | **Architecture:** Air-gapped single machine | **Hardware:** Standard CPU (No GPU required) |

---

## 1. Problem Statement and Pipeline Breakdown

In multi-contributor computer vision pipelines, trust breaks down across three distinct stages:

```
[1. Data Intake] ──────────► [2. Vendor / Pretrained Model] ──────────► [3. Production Inference]
Outside contributors pool    Vendor weights arrive with no record       Bounding box outputs sent downstream
COCO / YOLO batches without  of training provenance or clean lineage.   with no transit binding.
validation.
Risk: Poisoning, label       Risk: Silent weight substitution,          Risk: Replay attacks, output tampering,
flips, backdoor triggers.    trojans, hostile pickle deserialization.   broken chain of custody.
```

### Capability Comparison

| Capability | Manual / Ad-Hoc Review | Generic MLOps Monitoring | CipherLens |
|:---|:---|:---|:---|
| **Catches data poisoning / backdoors** | Only if a reviewer spots it manually | Rare, built for drift, not attacks | Spectral Signatures + Activation Clustering |
| **Checks model integrity (white / black box)** | Manual, one-off, not repeatable | Not covered | Neural Cleanse + STRIP, degrades gracefully |
| **Binds input, model, output cryptographically** | Not covered | Not covered | Ed25519 signing + Merkle-chained ledger |
| **Runs fully offline / air-gapped** | Depends on reviewer laptop | Usually requires cloud APIs | 100% offline pip wheelhouse |
| **Needs model retraining** | N/A | Often required | Zero-retraining baseline |

---

## 2. Technical Approach and Architecture

CipherLens executes as a self-contained, air-gapped security evaluation system on a single machine:

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
  * Spectral Signatures            * Neural Cleanse (white-box)     * MMD (multi-scale RBF)
  * Activation Clustering          * STRIP battery (black-box)      * 2-sample KS test
  * k-NN Label Consistency         * Weight spectral norm / kurt.   * Energy-OOD scoring
  * Perceptual Hash Dedup          * Access-tier honesty tag        * Separates benign vs adv.
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

### Core Tech Stack

* **Core ML & Detection:** PyTorch / TorchScript, ONNX Runtime, Adversarial Robustness Toolbox, Alibi Detect, scikit-learn, SciPy.
* **Cryptography & Governance:** Python `cryptography` (Ed25519, SHA-256), RFC 8785 JSON Canonicalization, JSON Schema (2020-12), SQLite Merkle audit ledger.
* **Data & Interface:** OpenCV, ImageHash, PyArrow (zero-copy memory mapped parsing), Streamlit UI.
* **Testing & Benchmarks:** NIST TrojAI, BackdoorBench, and dedicated repository red-team fixtures.

### Integrity Decision Tiers

* **Normal (ACCEPT):** Low aggregate risk score, zero critical findings. Auto-signs output and commits record as Accept.
* **Moderate (REVIEW):** Moderate anomaly detected (e.g. benign distribution drift or duplicate cluster). Flags anomaly and routes to analyst review.
* **Critical (QUARANTINE):** High-confidence backdoor, cryptographic signature tampering, or poisoning cluster. Automatically forces Quarantine disposition.

---

## 3. Empirical Test Results (Reproduced in Repo)

Every metric in the table below is directly computed from executed test runs in this repository:

| Capability / Benchmark | Target / PPT Claim | Test Suite Result | Verification Test File |
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

## 4. Step-by-Step App Usage Guide

You can run CipherLens locally or test it directly on the live deployment at [cipherlens.streamlit.app](https://cipherlens.streamlit.app).

All bundled sample fixtures reside in `data/samples/` and are pre-filled by default in the UI.

### Step 1: Launch the Application

```bash
# Clone the repository
git clone https://github.com/NehalAjmal/cipherlens.git
cd cipherlens

# Run virtual environment setup
bash scripts/setup_env.sh
source .venv/bin/activate

# Launch Streamlit UI
streamlit run cipherlens/ui/streamlit_app.py
```

The app opens locally at `http://localhost:8501`.

---

### Step 2: Home Page (Intake and Quick Start)

The Home page provides intake cards for each asset type and an end-to-end demo trigger:

1. **Option A: One-Click End-to-End Demo**
   * Scroll down to the **Quick Start** section.
   * Click **Run Full Demo**.
   * **What happens:** The pipeline loads the bundled COCO dataset sample (`data/samples/annotations/instances_samples.json`) and the ONNX model (`data/samples/resnet50_clean.onnx`), computes Data Integrity and Model Integrity, builds a cryptographically signed Assurance Report, commits it to the Merkle ledger, and automatically redirects you to the Assurance Report page.
2. **Option B: Step-by-Step Intake**
   * **Analyze a Dataset Card:**
     * Dataset File/Folder: `data/samples/annotations/instances_samples.json`
     * Images Directory: `data/samples/images`
     * Format: Select `COCO`
     * Click **Load Dataset**. A success toast confirms the dataset is active. Click **Go to Dataset Analysis ->**.
   * **Analyze a Model Card:**
     * Model File: `data/samples/resnet50_clean.onnx`
     * Optional toggle: Select **Simulate black-box access only** if you want to test graceful degradation on white-box models.
     * Click **Load Model**. The system reads the model manifest, hashes weights, resolves the access tier (`BLACK_BOX` or `WHITE_BOX`), and reveals **Go to Model Analysis ->**.
   * **Check an Inference Batch Card:**
     * Batch File: `data/samples/sample_inference_batch.jsonl`
     * Click **Load Batch**. A success toast confirms the batch is active. Click **Go to Inference Batch ->**.

---

### Step 3: Dataset Analysis Page (`pages/1_Dataset_Analysis.py`)

This page inspects training data for poisoning attacks, label noise, and contributor flooding.

1. Verify that your loaded dataset appears in the top summary bar (`instances_samples.json`, format `COCO`).
2. Click **Run Data Integrity Analysis**.
3. **What happens behind the scenes:**
   * Images pass through the reference frozen backbone (`models_cache/backbone/resnet18.pt`) to extract 512-dimensional embeddings.
   * **Spectral Signatures:** Computes SVD covariance decomposition per class and flags outliers with large projections along the top singular vector.
   * **Activation Clustering:** Performs dimension reduction and 2-cluster k-means to identify separated poison sub-populations.
   * **Label Consistency:** Evaluates k-NN cross-entropy agreement between image labels and feature space neighbors to flag label flips.
   * **Near-Duplicates:** Runs perceptual hash and cosine similarity to flag duplicate clusters.
   * **Contributor Risk:** Aggregates findings per contributor ID to catch coordinated Sybil poisoning.
4. **Inspect the results:**
   * **Overview tab:** Shows a bar chart of finding counts categorized by severity (`CRITICAL`, `HIGH`, `MEDIUM`) and a table of contributor-level risk. Select any finding ID in the dropdown to inspect the raw JSON evidence.
   * **Spectral Signature tab:** Displays anomalous feature representations.
   * **Label Consistency tab:** Displays candidates flagged for mislabeling.
   * **Near-Duplicates tab:** Displays duplicate image clusters.
5. Click **Add findings to Assurance Report** to queue all findings into the session report.

---

### Step 4: Model Analysis Page (`pages/2_Model_Analysis.py`)

This page evaluates the model for trojans and backdoors while enforcing access tier honesty.

1. Observe the top summary bar:
   * **Model:** `resnet50_clean.onnx`
   * **Format:** `ONNX`
   * **SHA-256:** Truncated 12-char digest matching the model manifest.
   * **Access Tier Badge:** `BLACK_BOX` (amber badge).
2. Note the degraded state warning banner:
   * *"Some checks are unavailable without white-box access. This assessment's confidence is bounded: see the report's access_tier field."*
   * This proves access tier honesty: black-box models are never falsely evaluated with white-box assumptions.
3. Click **Run Model Integrity Analysis**.
4. **Inspect the diagnostic tabs:**
   * **Tab 1: Neural Cleanse (White-Box Only):** Correctly displays *"Unavailable: black-box access only."* (When a PyTorch `.pt` model is loaded in white-box mode, this runs trigger size reconstruction and computes the MAD anomaly index).
   * **Tab 2: STRIP (Black-Box Battery):** Shows the results of the 50-step input perturbation battery. For `resnet50_clean.onnx`, it reports: *"No anomalously low-entropy inputs detected via STRIP"* because the model is clean and maintains high output entropy under perturbations.
   * **Tab 3: Weight Checks:** Correctly displays *"Unavailable: black-box access only."* (Weight kurtosis and spectral norm calculations require raw layer tensors).
5. Click **Add findings to Assurance Report** to queue model status into the report.

---

### Step 5: Inference Batch Page (`pages/3_Inference_Batch.py`)

This page checks cryptographic provenance across runtime inference logs to catch post-scoring tampering.

1. Ensure `data/samples/sample_inference_batch.jsonl` is loaded.
2. The page auto-verifies all 5 records on load using Ed25519 cryptographic signatures.
3. **Inspect the verification summary bar:**
   * **Records:** 5
   * **Verification Rate:** 80.0%
   * **Tamper Banner:** `1 record(s) failed signature verification: possible tampering detected.`
4. **Inspect individual records:**
   * Records 1, 2, 3, and 5 display green checkmarks (`✅`) confirming valid digital signatures.
   * Record 4 (`inf_0004`) displays a red cross (`❌`) because its bounding box confidence was tampered out-of-band after signing (modified from 0.82 to 0.99).
   * Open Record 4's expander to view the signature verification failure.
5. **Quarantine the tampered output:**
   * Click the red **Quarantine this record** button on Record 4.
   * A notification confirms: `Quarantined record inf_0004!`.
   * This generates a `PROVENANCE_TAMPERING` finding with `CRITICAL` severity and confidence 1.0.
6. Click **Add findings to Assurance Report** to include this tampering violation in the final report.

---

### Step 6: Assurance Report Page (`pages/4_Assurance_Report.py`)

This page presents the consolidated governance verdict for auditors and stakeholders.

1. **Review the Disposition Badge at the top:**
   * Shows the overall verdict: **`QUARANTINE`** (red badge).
   * Shows the aggregate continuous risk score.
   * **Why it triggered QUARANTINE:** The disposition engine uses a weighted sum of findings ($W_{INFO}=0, W_{LOW}=1, W_{MED}=3, W_{HIGH}=7, W_{CRIT}=15$). Any finding with severity `CRITICAL` and confidence >= 0.90 (such as the tampered inference record or poisoning cluster) immediately forces a `QUARANTINE` verdict.
2. **Review the Metrics Summary Cards:**
   * Spectral anomaly maximum score
   * Neural Cleanse MAD score
   * STRIP false positive rate
   * MMD drift statistic
   * Signature verification rate
3. **Inspect Findings Table:**
   * Complete table showing finding Category, Severity, Confidence, and Reason.
   * Click any finding row expander to view the exact JSON evidence payload.
4. **Export and Commit:**
   * Click **Download Assurance Report (JSON)** to save the complete report, strictly validated against `assurance_report_schema.json`.
   * Click **Sign & commit to Ledger** to append the report immutably into the SQLite Merkle ledger.

---

### Step 7: Audit Ledger Page (`pages/5_Audit_Ledger.py`)

This page demonstrates the append-only Merkle ledger and tamper localization.

1. **Inspect Ledger Entries:**
   * The table displays all committed assurance reports and provenance records with sequence index, asset type, payload type, and evaluation timestamp.
2. **Action 1: Verify Ledger Integrity**
   * Under the **Verify** column, click **Verify entire chain**.
   * The engine recalculates the complete Merkle tree over all entries.
   * Result: `Merkle tree integrity verified! Root: <64-char-hex>`.
3. **Action 2: External State Anchoring**
   * Under the **Anchoring** column, click **Export Checkpoint**.
   * The system exports a JSON checkpoint to `reports/checkpoints/checkpoint_<timestamp>.json` containing the latest Merkle root and record count.
   * This provides an out-of-band anchor that can be copied to a second storage device to guarantee external tamper-evidence.
4. **Action 3: Simulate Out-of-Band Database Tampering**
   * Under **Demo Tools**, locate the **Danger Zone** container.
   * Click **Simulate tampering (demo only)**.
   * This directly edits the SQLite database row on disk, altering record 2-of-3 to simulate an attacker trying to rewrite history.
   * Click **Verify entire chain**.
   * **Result:** The system immediately flags corruption and localizes the attack specifically to `Index [2]`, validating the PPT Slide 4 claim live!
   * Click **Restore demo ledger** to restore the clean database from backup.

---

## 5. Security Invariants and Architectural Guarantees

1. **Zero Outbound Network Calls:** Every assurance check runs 100% locally on CPU or local GPU. No telemetry, external API calls, or hosted model APIs exist on the runtime critical path.
2. **Safe Deserialization (`safe_torch_load`):** Arbitrary code execution via pickle deserialization is strictly blocked by enforcing `weights_only=True` across all PyTorch model loading sites, verified against a live malicious-pickle proof of concept.
3. **Canonical Cryptography:** All JSON serialization used for hashing adheres to RFC 8785 principles (`sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`) for deterministic SHA-256 digests and Ed25519 digital signatures.
4. **Weighted-Sum Risk Fusion:** Dispositions (`ACCEPT` / `REVIEW` / `QUARANTINE`) use continuous severity weights rather than simple boolean AND/OR gates that attackers can evade by suppressing single flags.
5. **Append-Only Merkle Ledger:** Ledger writes permit only append operations. Any direct modification to existing records breaks root verification and pinpoints the exact corrupted sequence index.
6. **Graceful Degradation:** When evaluating black-box models, unavailable white-box checks are explicitly documented in the report schema rather than silently dropped or faked.

---

## 6. Complete Documentation Directory

All specifications and architectural contracts are maintained in [`docs/`](docs/):

* [`docs/PRD.md`](docs/PRD.md): Product Requirements Document and problem scope contracts
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Module isolation rules, import hierarchy, and system layout
* [`docs/COVERAGE_STATEMENT.md`](docs/COVERAGE_STATEMENT.md): Empirical attack detection coverage statement
* [`docs/VALIDATION_TRAIL.md`](docs/VALIDATION_TRAIL.md): Log of 15 code review findings (8 critical, 7 architectural)
* [`docs/BACKEND_SCHEMA.md`](docs/BACKEND_SCHEMA.md): Complete JSON schema definitions and Merkle ledger schema
* [`docs/APP_FLOW.md`](docs/APP_FLOW.md): Streamlit UI states, pages, and interactive button linkages
* [`docs/TRD.md`](docs/TRD.md): Technical requirements, hardware baseline, and open-source dependency audit

---

## 7. License and Open-Source Compliance

Distributed under the Apache 2.0 / MIT Open Source License. All dependencies are open-source and free, requiring no paid tier or API key.
