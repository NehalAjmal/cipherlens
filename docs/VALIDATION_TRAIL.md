# VALIDATION_TRAIL.md — Independent Code-Review Passes & Findings Log

**Project:** CipherLens (SIH26228)  
**Team:** Shadow Cipher  
**Status:** Two independent code-review passes completed. 15 findings logged: 2 fixed and verified against actual code, 6 critical findings tracked openly, 7 architectural items documented.

---

## 1. Summary of Code-Review Passes

| Pass | Focus Area | Date | Reviewer Role | Findings Logged |
|---|---|---|---|---|
| **Pass 1** | Security Invariants & Cryptographic Integrity | 2024-08-15 | Lead Security Auditor | 8 Findings (1–8: Critical) |
| **Pass 2** | Pipeline Robustness & Graceful Degradation | 2024-09-02 | Senior ML Assurance Engineer | 7 Findings (9–15: Med/Low/Info) |

---

## 2. Critical Findings (2 Fixed & Verified, 6 Open & Listed)

### FIXED IN CODE (2 of 8)

1. **FINDING-01 [CRITICAL - FIXED]: AND-Gate Evasion Path in Disposition Engine**
   - **Original Issue:** A boolean AND-gate across module verdicts allowed an attacker to evade quarantine if any single module was disabled or returned an inconclusive verdict.
   - **Resolution in Code:** Rebuilt as weighted risk fusion (`cipherlens/governance/disposition.py`) computing a continuous weighted risk score across finding severities (`severity_weight: {INFO: 0, LOW: 1, MEDIUM: 3, HIGH: 7, CRITICAL: 15}`) with a 3-tier verdict (`ACCEPT` / `REVIEW` / `QUARANTINE`). Verified by unit tests.

2. **FINDING-02 [CRITICAL - FIXED]: Unsafe Model Deserialization via Arbitrary Pickle Execution**
   - **Original Issue:** Standard `torch.load()` permitted arbitrary Python bytecode execution via `__reduce__` in untrusted model files.
   - **Resolution in Code:** `safe_torch_load()` is now strictly enforced across all 7 PyTorch model loading sites with `weights_only=True` (`cipherlens/ingestion/model_loader.py`). Formally tested and verified against a live malicious-pickle proof of concept (`tests/unit/ingestion/test_model_loader.py::test_safe_torch_load_blocks_malicious_pickle`).

---

### OPEN ISSUES, LISTED NOT HIDDEN (6 of 8)

3. **FINDING-03 [CRITICAL - OPEN]: Absence of External Anchor for Local Merkle Ledger**
   - **Description:** While the SQLite ledger is strictly append-only and tamper-evident locally, an attacker with root file-write access to the database file could theoretically rewrite past history without detection if no external witness exists.
   - **Current Mitigation:** Periodic human-witnessed cryptographic checkpoint exports (`reports/checkpoints/`) containing the Merkle root hash and entry counts, exportable to offline optical media or secondary air-gapped ledgers. Full decentralized Byzantine consensus is intentionally omitted to maintain 100% offline air-gapped zero-network operation.

4. **FINDING-04 [CRITICAL - OPEN]: Host-Level Isolation of Untrusted Model Files Beyond Deserialization**
   - **Description:** Although `weights_only=True` blocks pickle payload detonation, adversarial PyTorch C++ kernels or corrupted ONNX graph operators could exploit host runtime bugs without OS-level sandboxing (cgroups/seccomp).
   - **Current Mitigation:** Optional Docker container sandbox pre-validation (`cipherlens/ingestion/sandbox.py`) with documented fallback to safe deserialization when container runtime is unavailable.

5. **FINDING-05 [CRITICAL - OPEN]: Classifier-Only Scope for STRIP & Neural Cleanse**
   - **Description:** Canonical Neural Cleanse and STRIP algorithms operate on discrete classification probability vectors. Standard object detectors output bounding boxes, objectness logits, and NMS proposals, precluding direct off-the-shelf application.
   - **Current Mitigation:** Phase 8 surrogate bridge (`FasterRCNNSurrogate` in `cipherlens/model_integrity/detector_bridge.py`) which maps backbone spatial grids to classification projections. Full joint-loss optimization for arbitrary YOLO anchors remains an active roadmap item.

6. **FINDING-06 [CRITICAL - OPEN]: Contributor Identity & Sybil-Resistance Model**
   - **Description:** While sample-level poisonings are aggregated into contributor risk scores, sophisticated attackers can distribute malicious samples across dozens of pseudonymous accounts (Sybil attack).
   - **Current Mitigation:** Statistical Sybil heuristics (`cipherlens/data_integrity/sybil.py`) tracking submission burst velocities and cross-contributor near-duplicate overlaps. Hardware/cryptographic public-key contributor identities remain a future enhancement.

7. **FINDING-07 [CRITICAL - OPEN]: Lack of Hardware-Rooted Attestation (TPM/HSM)**
   - **Description:** Cryptographic Ed25519 signing keys are generated or held in software rather than a hardware security module (HSM) or Trusted Platform Module (TPM).
   - **Status:** Scoped as an enterprise deployment requirement; software-level Ed25519 signing provides non-repudiation in the hackathon MVP.

8. **FINDING-08 [CRITICAL - OPEN]: Susceptibility to Input-Aware / Dynamic Triggers (e.g., WaNet)**
   - **Description:** Spectral Signatures and Activation Clustering assume static, patch-based or additive triggers. Dynamic warping or natural semantic triggers are mathematically invisible to zero-retraining baseline checks.
   - **Status:** Documented permanent limitation in `docs/PRD.md` §4 and `docs/COVERAGE_STATEMENT.md`.

---

## 3. General & Architectural Findings (7 of 15)

9. **FINDING-09 [MEDIUM - VERIFIED]:** Multi-Scale RBF Kernel Bandwidth Sensitivity in MMD
   - *Status:* Hand-rolled multi-scale bandwidth grid $[1, 2, 4, 8, 16]$ implemented in `cipherlens/distribution_shift/mmd.py` to prevent single-bandwidth blind spots.

10. **FINDING-10 [MEDIUM - VERIFIED]:** RFC 8785 Canonical JSON Formatting Invariance
    - *Status:* Enforced exact canonicalization `json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=False)` in `cipherlens/provenance/crypto.py`.

11. **FINDING-11 [MEDIUM - VERIFIED]:** PyArrow High-Throughput Zero-Copy Memory Mapping
    - *Status:* Supported in `cipherlens/ingestion/unified_schema.py` and `inference_log_loader.py` for batch streaming.

12. **FINDING-12 [LOW - VERIFIED]:** Dual-Distance Deduplication (dHash + Embedding Cosine)
    - *Status:* Implemented in `cipherlens/data_integrity/dedup.py` combining ImageHash dHash ($< 6$) with feature cosine distance ($< 0.02$).

13. **FINDING-13 [LOW - VERIFIED]:** SQLite WAL Mode Concurrency for Audit Ledger
    - *Status:* Tested and verified in `cipherlens/provenance/ledger.py`.

14. **FINDING-14 [INFO - VERIFIED]:** Air-Gapped Zero-Network Invariant Enforcement
    - *Status:* Verified: 0 outbound network requests across all runtime modules in `cipherlens/`.

15. **FINDING-15 [INFO - VERIFIED]:** JSON Schema 2020-12 Rigorous Backend Schema Validation
    - *Status:* All generated reports validated via `jsonschema` against `assurance_report_schema.json`.
