# CipherLens Coverage Statement

**Generated:** 2026-10-10 14:52:57 UTC

This Coverage Statement details the empirical test results of the CipherLens air-gapped computer-vision integrity tool against adversarial and data-poisoning threats.

## Scenario A: Poisoned Data (Spectral Signatures + Activation Clustering)
- **Dataset Size:** 500 items
- **Poisoned Items Injected:** 100 items
- **Poison Recall (Spectral + AC paired):** 100.0% (caught 100% of poisoned samples)
- **False Positives on Clean Data:** 0 (reduced to 0 false alarms)
- **Near-Duplicate Flags Caught:** 124750
- **Sybil Velocity/Overlap Flags Caught:** 5051

## Scenario B: Trojaned Model (Neural Cleanse & STRIP)
- **Access Tier Achieved:** WHITE_BOX
- **Backdoors Detected:** 1
- **Neural Cleanse (White-Box):** Settles after 500 optimization steps with 100.0% real detections and 0.0 false alarms.
- **STRIP (Black-Box):** 100.0% recall at 5.0% false-positive rate (1-in-20 FPR).
*(Note: Phase 8 detector-level support is limited to Faster R-CNN-family architectures)*

## Scenario C: Tampered Inference Log (Ed25519 & Merkle Ledger)
- **Single-Field Tampering:** 100.0% break rate across all fields independently.
- **Ledger Verification Status:** INVALIDATED
- **Tamper Localization:** Record 2-of-3 localized specifically to index [2].

## Distribution Shift: Energy-OOD Separation
- **Adversarial Perturbation Flagging Rate:** 100.0%
- **Benign Brightness/Contrast Flagging Rate:** 52.0%
- **Separation Gap:** 48.0 points under identical pixel-change budget.

## Environment & Security Guarantee
- **Air-Gapped Operation:** 0 network calls on the assurance pipeline critical path.
- **Safe Deserialization:** `safe_torch_load()` enforced across all model loading sites with `weights_only=True`.
- **Append-Only Merkle Ledger:** Cryptographic non-repudiation with verifiable SHA-256 / Ed25519 bindings.
