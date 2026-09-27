# BACKEND_SCHEMA.md — The Data Layer

Every shape of data that moves through CipherLens, defined once here, implemented exactly this way in code. No module invents its own ad-hoc dict shape — if it needs a new field, this file is updated first.

---

## 1. Storage overview

| What | Where | Format |
|---|---|---|
| Raw input datasets | `data/raw/<source>/` | Untouched COCO JSON or YOLO txt+images, as received |
| Normalized dataset items (in-memory / cached) | `data/samples/*.parquet` or `.jsonl` (cache only, not source of truth) | See §2 |
| Downloaded/cached models | `models_cache/<model_id>/` | Original `.pt`/`.onnx` file + a `manifest.json` with its SHA-256 |
| Generated Assurance Reports | `reports/assurance/<report_id>.json` | Validated against `assurance_report_schema.json` |
| Audit ledger | `reports/ledger.sqlite3` | SQLite table, see §5 |
| Provenance records (per-inference) | `reports/provenance/<batch_id>.jsonl` | One JSON object per line, see §4 |

Everything under `reports/` and `models_cache/` is gitignored (regenerated per run) except `.gitkeep`/`README.md` placeholders. Only `data/samples/` (tiny, non-sensitive) is committed, for reproducible tests.

---

## 2. Unified dataset item schema (`ingestion/unified_schema.py`)

```json
{
  "item_id": "string (stable hash of image path + contributor_id)",
  "image_path": "string (relative to data/raw/)",
  "image_sha256": "string, 64 hex chars",
  "width": "int",
  "height": "int",
  "annotations": [
    {
      "category_id": "int",
      "category_name": "string",
      "bbox_xywh": ["float", "float", "float", "float"],
      "segmentation": "optional, list of polygons"
    }
  ],
  "contributor_id": "string",
  "batch_id": "string",
  "source_format": "COCO | YOLO",
  "acquisition_meta": {
    "timestamp": "ISO-8601 string, optional",
    "sensor": "string, optional",
    "notes": "string, optional"
  }
}
```

---

## 3. Model handle (`ingestion/model_loader.py`)

Not serialized to disk as-is (it wraps a live PyTorch/ONNX runtime object); the **manifest** that IS persisted:

```json
{
  "model_id": "string",
  "format": "PYTORCH | ONNX",
  "file_path": "string",
  "sha256": "string, 64 hex chars",
  "architecture_hint": "string, e.g. 'resnet18' or 'unknown'",
  "num_parameters": "int, optional",
  "loaded_at": "ISO-8601 string",
  "access_tier_available": "WHITE_BOX | BLACK_BOX"
}
```

---

## 4. Inference Provenance Record (`provenance/crypto.py` output — matches your PPT's design exactly)

```json
{
  "version": "1.0-ed25519",
  "timestamp_utc": "ISO-8601 string",
  "nonce": "string, unique per record (uuid4 hex)",
  "digests": {
    "image_sha256": "64 hex chars — over shape+dtype+raw buffer",
    "model_sha256": "64 hex chars — over full model file bytes",
    "config_sha256": "64 hex chars — over canonical JSON of preprocessing+runtime config",
    "output_sha256": "64 hex chars — over canonical JSON of sorted detections",
    "root_sha256": "64 hex chars — SHA-256(image:model:config:output:nonce:timestamp)"
  },
  "public_key_hex": "string, 64 hex chars (Ed25519 raw public key)",
  "signature_base64": "string (Ed25519 signature over root_sha256)"
}
```
**Canonicalization rule:** all JSON used for hashing is serialized with `sort_keys=True, separators=(',', ':'), ensure_ascii=False` — this is non-negotiable; any deviation breaks reproducible verification. Reference implementation: the Python code already in your Gemini design doc (`InferenceProvenanceEngine`) — Phase 1 of PLAN.md builds exactly this, unmodified in its cryptographic core.

---

## 5. Audit Ledger (SQLite table, `provenance/ledger.py`)

```sql
CREATE TABLE ledger_entries (
    seq_index       INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id        TEXT NOT NULL UNIQUE,       -- uuid4
    entry_type      TEXT NOT NULL,              -- 'ASSURANCE_REPORT' | 'PROVENANCE_RECORD'
    payload_sha256  TEXT NOT NULL,              -- hash of the JSON payload this entry commits to
    payload_path    TEXT NOT NULL,              -- where the full payload is stored (reports/...)
    prev_hash       TEXT NOT NULL,              -- hash of the previous entry's leaf (Merkle chain link)
    leaf_hash       TEXT NOT NULL,              -- SHA-256(prev_hash || payload_sha256 || seq_index)
    merkle_root_at_write TEXT NOT NULL,         -- running Merkle root at time of this write
    created_at      TEXT NOT NULL,              -- ISO-8601
    witness_export_id TEXT                      -- NULL until included in a checkpoint export, see §5.1
);
```
- `merkle.py` recomputes the tree over all `leaf_hash` values on demand for verification; `ledger.py` never trusts `merkle_root_at_write` blindly — every read verifies it.
- **Editing localization property (must hold, tested in `tests/unit/provenance/test_merkle.py`):** mutating `payload_path`'s file content for entry N changes `payload_sha256`, which is detectable by recomputing and comparing against `leaf_hash` for exactly index N — not a generic "tree changed" flag.

### 5.1 Checkpoint export (the practical answer to "external anchoring," see ARCHITECTURE.md §"why")
Periodically (config-driven, e.g. every N entries or on demand from the UI), `ledger.py` writes a signed checkpoint file `reports/checkpoints/checkpoint_<timestamp>.json` containing `{merkle_root, entry_count, signature}`. The human's job (see HUMAN_TASKS.md) is to copy this file off-machine (USB, second device, printed QR — anything outside the operator's own write access) periodically. This is a real, honest, air-gap-compatible answer to "an attacker with ledger write access could still rewrite history" — it doesn't eliminate the risk, it bounds it to "since the last exported checkpoint," which is exactly the kind of precise, defensible limitation a Coverage Statement should state.

---

## 6. Findings object (shared shape used by all four assessment modules before governance merges them)

```json
{
  "finding_id": "string, uuid4",
  "category": "DATA_POISONING | LABEL_FLIP | NEAR_DUPLICATE | MODEL_BACKDOOR | WEIGHT_TAMPER | PROVENANCE_TAMPERING | DISTRIBUTION_SHIFT",
  "severity": "INFO | LOW | MEDIUM | HIGH | CRITICAL",
  "confidence": "float 0.0-1.0",
  "reason": "human-readable string",
  "evidence": {
    "...": "category-specific: e.g. spectral_anomaly_score, neural_cleanse_mad_score, mmd_statistic, ks_p_value"
  },
  "affected_elements": ["string ids: item_id(s), contributor_id, model_id, batch_id"],
  "access_tier": "WHITE_BOX | BLACK_BOX | N/A",
  "disposition": "ACCEPT | REVIEW | QUARANTINE"
}
```

---

## 7. Assurance Report (`governance/schema/assurance_report_schema.json`)

This is the canonical top-level document. It is **exactly** the schema already validated in your Gemini design doc (reproduced here as the single source of truth — code must import and validate against this literal file, never a re-typed copy):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CVIntegrityAssuranceReport",
  "type": "object",
  "required": ["report_id", "evaluation_timestamp", "asset_metadata", "access_tier",
               "overall_disposition", "findings", "metrics_summary", "tamper_evident_audit_record"],
  "properties": {
    "report_id": { "type": "string", "format": "uuid" },
    "evaluation_timestamp": { "type": "string", "format": "date-time" },
    "asset_metadata": {
      "type": "object",
      "required": ["asset_type", "asset_identifier", "asset_sha256"],
      "properties": {
        "asset_type": { "type": "string", "enum": ["DATASET", "MODEL", "INFERENCE_BATCH"] },
        "asset_identifier": { "type": "string" },
        "asset_sha256": { "type": "string", "pattern": "^[a-fA-F0-9]{64}$" },
        "format": { "type": "string", "enum": ["COCO", "YOLO", "ONNX", "PYTORCH", "JSONL"] },
        "config_hash": { "type": "string", "description": "hash of configs/default.yaml used for this run" }
      }
    },
    "access_tier": { "type": "string", "enum": ["WHITE_BOX", "BLACK_BOX"] },
    "overall_disposition": { "type": "string", "enum": ["ACCEPT", "REVIEW", "QUARANTINE", "REJECT"] },
    "findings": { "type": "array", "items": { "$ref": "#/$defs/finding" } },
    "metrics_summary": {
      "type": "object",
      "properties": {
        "spectral_anomaly_max": { "type": "number" },
        "neural_cleanse_mad_score": { "type": ["number", "null"] },
        "strip_false_positive_rate": { "type": ["number", "null"] },
        "mmd_drift_statistic": { "type": "number" },
        "ks_p_value": { "type": ["number", "null"] },
        "signature_verification_rate": { "type": "number" }
      }
    },
    "tamper_evident_audit_record": {
      "type": "object",
      "required": ["merkle_root", "signature", "signing_key_id"],
      "properties": {
        "merkle_root": { "type": "string", "pattern": "^[a-fA-F0-9]{64}$" },
        "signature": { "type": "string" },
        "signing_key_id": { "type": "string" }
      }
    }
  },
  "$defs": {
    "finding": {
      "type": "object",
      "required": ["finding_id", "category", "severity", "confidence", "reason", "evidence", "disposition"],
      "properties": {
        "finding_id": { "type": "string" },
        "category": { "type": "string", "enum": ["DATA_POISONING", "LABEL_FLIP", "NEAR_DUPLICATE",
                        "MODEL_BACKDOOR", "WEIGHT_TAMPER", "PROVENANCE_TAMPERING", "DISTRIBUTION_SHIFT"] },
        "severity": { "type": "string", "enum": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] },
        "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
        "reason": { "type": "string" },
        "evidence": { "type": "object" },
        "affected_elements": { "type": "array", "items": { "type": "string" } },
        "disposition": { "type": "string", "enum": ["ACCEPT", "REVIEW", "QUARANTINE"] }
      }
    }
  }
}
```
Note: `access_tier` at the report root reflects the model-integrity assessment's access level; individual findings also carry `access_tier` per §6, since a report may combine model-integrity (WHITE_BOX) with data-integrity (N/A — access tier only meaningfully applies to model assessment).

---

## 8. Disposition weighting (the fix for the "AND-gate evasion" bug your PPT already found and fixed)

`governance/disposition.py` computes overall disposition as a **weighted sum**, never a boolean AND/OR of module verdicts:

```
risk_score = Σ (severity_weight[finding.severity] × finding.confidence)   over all findings
severity_weight = { INFO: 0, LOW: 1, MEDIUM: 3, HIGH: 7, CRITICAL: 15 }   # tunable in configs/default.yaml

if risk_score >= config.quarantine_threshold: overall = QUARANTINE
elif risk_score >= config.review_threshold:   overall = REVIEW
else:                                          overall = ACCEPT
```
Any single `CRITICAL` finding with `confidence >= 0.9` force-overrides to `QUARANTINE` regardless of total score (a documented, explicit override, not an implicit AND-gate).

---

## 9. Config schema (`configs/default.yaml` — validated by `config.py` via pydantic)

```yaml
execution:
  parallel: true
  device: "cpu"          # "cpu" | "cuda" (cuda optional, never required)

thresholds:
  spectral_signature_iqr_multiplier: 1.5
  dedup_cosine_distance_max: 0.02
  neural_cleanse_anomaly_index_min: 2.0
  strip_perturbation_grid: 10
  mmd_kernel_bandwidths: [1, 2, 4, 8, 16]
  energy_ood_temperature: 1.0

disposition:
  severity_weight: { INFO: 0, LOW: 1, MEDIUM: 3, HIGH: 7, CRITICAL: 15 }
  review_threshold: 5
  quarantine_threshold: 12
  critical_override_confidence: 0.9

ledger:
  checkpoint_every_n_entries: 25
  db_path: "reports/ledger.sqlite3"

paths:
  backbone_cache: "models_cache/backbone/"
  reports_dir: "reports/assurance/"
```
