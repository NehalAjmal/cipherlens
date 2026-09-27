# PRD.md — Product Requirements Document

**Product:** CipherLens
**One-liner:** An offline, air-gapped assurance layer that cryptographically and statistically proves whether the training data, model weights, and inference outputs in a multi-contributor computer-vision pipeline can be trusted — without requiring retraining or full white-box access.

This document is the contract. If a feature isn't in "In Scope," it does not get built without a deliberate, written amendment to this file. This is what stops scope creep.

---

## 1. Background (from the problem statement, condensed)

Multi-contributor CV pipelines combine data from many sources, pretrained/vendor models, and produce inference outputs consumed downstream. Three trust gaps exist:
1. **Data intake:** pooled COCO/YOLO batches from outside contributors, unchecked → poisoning, label flips, backdoor triggers.
2. **Vendor/pretrained models:** PyTorch/ONNX weights with no record of provenance → silent substitution, trojaned weights.
3. **Inference in production:** bounding-box outputs sent downstream with no tamper-proofing → replay, tampering, no cryptographic binding.

CipherLens closes this gap end-to-end with an evidence-based assurance report.

---

## 2. Users / who this is for

| Persona | What they get |
|---|---|
| ML engineer / data team | Runs CipherLens on a new data batch or model before it enters the pipeline; gets an Accept/Review/Quarantine verdict with evidence, no retraining needed for the baseline check. |
| Downstream automated system | Verifies a signed inference record before trusting a bounding box. |
| Compliance / auditor | Reads the Merkle-chained audit ledger and per-asset Assurance Report for regulatory review. |
| Defense / air-gapped operator | Runs the entire tool with zero network dependency. |
| Contributor / vendor | Gets an evidence-based verdict instead of a blanket ban. |

---

## 3. In scope — what CipherLens IS

### 3.1 Core capabilities (all five, as required by the problem statement)
1. **Training-Data Integrity** — detect trigger injection/backdoor patterns (Spectral Signatures + Activation Clustering), label flipping / systematic mislabeling (k‑NN label-entropy consistency), near-duplicate flooding (perceptual hashing + embedding cosine distance), and aggregate sample-level findings into contributor-level risk scores.
2. **Model Integrity** — white-box backdoor detection via Neural Cleanse-style trigger reconstruction + activation/weight statistics; black-box fallback via STRIP-style perturbation testing; explicit statement of which access tier was used and what confidence that implies. Runs against classification heads/backbones at MVP; a bounding-box/objectness extension is a documented stretch goal (see PLAN.md Phase 8).
3. **Inference Provenance & Output Integrity** — SHA-256 digests of image, model weights, execution config, and output; Ed25519 signature over the combined root hash; tamper detection on any post-hoc alteration.
4. **Distribution-Shift & Anomaly Assessment** — MMD (multi-scale RBF kernel) + two-sample KS test + Energy-based OOD score, used together to distinguish benign operational drift from adversarial manipulation.
5. **Analyst-Facing Governance** — every finding carries reason, evidence, severity, confidence, affected asset, recommended disposition; Merkle-chained tamper-evident audit ledger; offline Streamlit dashboard; schema-validated JSON Assurance Report.

### 3.2 Hardening / stretch items (explicitly kept in scope per your instruction, phased later — see PLAN.md Phases 8–10)
- Extending backdoor detection from classification-only to detector (bbox/NMS) outputs.
- External/witnessed anchoring for the Merkle ledger beyond a single local store.
- Sandboxed execution for untrusted model files beyond safe deserialization.
- Contributor identity / Sybil-resistance handling on top of contributor-level risk aggregation.

### 3.3 Supported formats
- Datasets: **COCO** (JSON annotations) and **YOLO** (txt label files) — normalized into one internal schema.
- Models: **PyTorch** (`.pt`, `.pth`, TorchScript) and **ONNX** (`.onnx`).
- Inference logs: **JSONL**.

### 3.4 Non-functional requirements
- **100% offline at run time**, zero outbound network calls on the assurance pipeline's critical path. (Setup/install requires internet once — see 00_READ_ME_FIRST §2.3.)
- **No retraining required** for the baseline integrity assessment.
- **Graceful degradation**: if only black-box access is available, the system runs the black-box battery and *says so* in the report rather than failing.
- Runs on a single machine, CPU-only, cross-platform (Windows/macOS/Linux).
- Every dependency is free and open-source (see TRD.md).

### 3.5 Definition of Done (hackathon submission)
Per the problem statement's "Expected Solution," a complete submission has:
- [ ] Source code (this repo, built via PLAN.md phases 0–7 minimum).
- [ ] Architecture and setup notes (ARCHITECTURE.md + README derived from it).
- [ ] The Assurance-Report JSON Schema (BACKEND_SCHEMA.md → `schema/assurance_report_schema.json`).
- [ ] A reproducible audit log (Merkle ledger populated by an actual demo run, not fabricated).
- [ ] A clear Coverage Statement: supported attack classes, assumptions, and known limitations — written honestly from real test results (Phase 11), matching the style already on your feasibility slide.
- [ ] Red-team scenarios A (poisoned data), B (trojaned model), C (tampered inference) scripted and passing against team-generated test fixtures.

---

## 4. Out of scope — what CipherLens is explicitly NOT

Even with the hardening items kept on the long-term roadmap, the following are **not** part of this build, full stop, because they are different products or research programs, not engineering tasks a hackathon team can ship:

- **Not a training pipeline.** CipherLens never trains or fine-tunes a production model. (It may fine-tune a small proxy classifier strictly for Neural Cleanse/STRIP testing purposes — that is tooling, not a product feature.)
- **Not a general-purpose MLOps monitoring platform.** No experiment tracking, no model registry UI beyond what's needed to store digests, no CI/CD integration.
- **Not a real-time video/streaming inference guard.** Works on batches of images and JSONL inference logs, not live camera feeds.
- **Not a multi-user web SaaS.** No login system, no user accounts, no roles/permissions beyond the single-operator Streamlit session. (Contributor identity in the risk-scoring sense is different from user auth — see 3.2.)
- **Not a mobile app.** Desktop/laptop only.
- **Not a defense against every attack class.** Dynamic/input-aware backdoors (e.g., WaNet), semantic natural backdoors, and physical-world adversarial evasion prior to camera capture are mathematically out of reach for a zero-retraining, degrade-gracefully system — this is stated as a permanent, honest limitation in the Coverage Statement, not a bug.
- **Not a blockchain product.** "Merkle-chained ledger" means a local, verifiable hash chain — not a distributed public blockchain, a token, or a smart contract.
- **Not a general image-editing / annotation tool.** It consumes existing COCO/YOLO annotations; it does not provide an annotation UI.
- **Not dependent on any paid API, cloud account, or license.** If a feature would require one, it does not go into this product — find a free/offline alternative or cut the feature (see TRD.md §2 for the free-ness audit of every dependency actually used).

If mid-build you (or Antigravity) find yourselves about to build something in this "Out of scope" list, stop — that's scope creep. Update this PRD first, deliberately, before writing code.

---

## 5. Success metrics (what "working" means, concretely)

These are the same targets your PPT already claims — the build's job is to actually produce them from a real run, not restate them:

| Capability | Target metric | How verified |
|---|---|---|
| Data integrity | High recall on team-injected poisoned samples, low false-positive rate after Activation Clustering pass | `tests/redteam/test_scenario_a_poisoned_data.py` |
| Model integrity (white-box) | Correct target-class identification via Neural Cleanse Anomaly Index > threshold | `tests/redteam/test_scenario_b_trojaned_model.py` |
| Model integrity (black-box) | STRIP flags the backdoored model at an acceptable false-positive rate | same suite, black-box path |
| Provenance | Any single-field post-signing alteration reliably fails verification, every time | `tests/redteam/test_scenario_c_modified_inference.py` |
| Ledger | Editing any one record in the Merkle ledger is localized to that exact index | `tests/unit/test_merkle_ledger.py` |
| Distribution shift | Adversarial-perturbation OOD score measurably separated from benign brightness/contrast shift at equal pixel-change budget | `tests/integration/test_distribution_shift.py` |

---

## 6. Assumptions & constraints

- Team-generated or small public datasets are acceptable test fixtures (explicitly allowed by the problem statement — "publicly available **or team-generated** datasets and models").
- A frozen, pretrained, ImageNet-scale backbone (ResNet‑18 or MobileNetV3, via `torchvision`) stands in for "Φ(·)," the reference feature extractor, per the Gemini design doc.
- The reference/demo dataset is small (hundreds of images) — this is a hackathon proof-of-concept, not a production-scale deployment; the Coverage Statement says this explicitly.
- CPU-only execution is the baseline target; GPU is an optional speed-up, never a requirement.

---

## 7. Open questions to resolve before/at Phase 0 (see HUMAN_TASKS.md)
- Which demo dataset will you actually use (a COCO subset you already have, or a fresh small set you'll assemble)? A default is proposed in HUMAN_TASKS.md if you have no preference.
- Team size / who owns which phase (affects whether phases run sequentially or in parallel across teammates — PLAN.md assumes sequential-by-default but notes where parallel split is safe).
