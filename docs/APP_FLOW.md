# APP_FLOW.md — Every Screen, State, Button, Linkage

CipherLens's UI is a local Streamlit multipage app (`streamlit run cipherlens/ui/streamlit_app.py`). This document is exhaustive enough that Antigravity should never need to invent a screen, button, or state that isn't listed here.

---

## 0. Global shell (present on every page)
- **Sidebar (always visible):**
  - CipherLens logo/title + "100% Offline" badge (static text, always shown, reinforces the claim).
  - Page navigation (Streamlit's native multipage nav from `ui/pages/`): Home, Dataset Analysis, Model Analysis, Inference Batch, Assurance Report, Audit Ledger.
  - "Current session" panel: shows which dataset/model/batch is currently loaded (from `st.session_state`), with a "Clear session" button.
  - Config indicator: shows the active `configs/default.yaml` hash + a "View config" expander (read-only in MVP; editing config is a file-edit task, not a UI feature, to avoid building a second source of truth).
- **Top-of-page:** breadcrumb-style page title + one-line description of what this page does.
- **Global state object** (`st.session_state`), fields: `loaded_dataset`, `loaded_model`, `loaded_inference_batch`, `last_report_id`, `access_tier`. Every page reads/writes only its relevant subset — no page should need to know about another page's internals.

---

## 1. Home / Landing page (`streamlit_app.py`)

**Purpose:** entry point, quick health check, and the three intake actions.

**Layout:**
- Header: "CipherLens — Trustworthy CV Integrity Assurance" + one-sentence description.
- Three cards, side by side (or stacked on narrow screens):
  1. **"Analyze a Dataset"** — file/folder picker (COCO JSON or YOLO folder) → button **"Load Dataset"** → on success, sets `session_state.loaded_dataset`, shows a green toast, and reveals a **"Go to Dataset Analysis →"** button.
  2. **"Analyze a Model"** — file picker (`.pt`/`.pth`/`.onnx`) → button **"Load Model"** → on success, detects format + access tier (white-box if PyTorch/TorchScript with accessible weights, black-box if ONNX-only or explicitly restricted via a toggle "Simulate black-box access only") → reveals **"Go to Model Analysis →"**.
  3. **"Check an Inference Batch"** — JSONL file picker → button **"Load Batch"** → on success, shows record count → reveals **"Go to Inference Batch →"**.
- Below the cards: **"Run Full Demo"** button — runs `scripts/run_demo.py`'s scenario end-to-end against the bundled `data/samples/` fixtures, for judges who want one click. Shows a progress bar, then redirects to the Assurance Report page.
- Footer: link to `docs/COVERAGE_STATEMENT.md` rendered inline (what this tool does and does not detect) — always visible, never hidden, matching the "listed not hidden" ethos from your PPT.

**States:** `empty` (nothing loaded) → `loading` (spinner on the active card) → `loaded` (success toast + nav button) → `error` (red inline message with the specific exception, e.g. "Unsupported YOLO folder structure: no `labels/` directory found").

---

## 2. Dataset Analysis page (`pages/1_Dataset_Analysis.py`)

**Precondition:** `session_state.loaded_dataset` is set (else: shows "No dataset loaded" + button back to Home).

**Layout:**
- Summary bar: item count, contributor count, batch count, source format.
- **"Run Data Integrity Analysis"** button → triggers `data_integrity.analyze(...)` (spinner: "Running Spectral Signatures... Running Activation Clustering... Checking near-duplicates... Aggregating contributor risk...", each stage updates the spinner text so it's visibly not a fake progress bar).
- Results, in tabs:
  - **Tab "Overview"**: bar chart of finding counts by severity; contributor-level risk table (sortable), each row clickable to drill into that contributor's flagged items.
  - **Tab "Spectral Signature"**: scatter/histogram of anomaly scores per class, threshold line drawn, flagged points highlighted.
  - **Tab "Label Consistency"**: table of flagged label-flip candidates (image thumbnail, predicted-vs-labeled class, entropy score).
  - **Tab "Near-Duplicates"**: grid of duplicate clusters (thumbnails side by side).
- **"Add findings to Assurance Report"** button → calls `governance.report_builder`, updates `session_state.last_report_id`, shows toast with link to Assurance Report page.

**States:** `no_dataset` → `loaded_not_analyzed` → `analyzing` → `analyzed` (tabs populated) → `error` (per-stage error shown inline in that tab, other tabs still populate — this is the "graceful degradation" requirement made visible in the UI).

---

## 3. Model Analysis page (`pages/2_Model_Analysis.py`)

**Precondition:** `session_state.loaded_model` set.

**Layout:**
- Summary bar: model format, SHA-256 (truncated + "copy full hash" button), detected access tier badge (WHITE_BOX green / BLACK_BOX amber).
- Access tier override: toggle "Force black-box mode" (lets a user demo graceful degradation deliberately even on a white-box-capable model).
- **"Run Model Integrity Analysis"** button → runs the tier-appropriate battery.
- Results, in tabs:
  - **Tab "Neural Cleanse" (white-box only; shows "Unavailable — black-box access only" message otherwise, not an error)**: per-class Anomaly Index bar chart, reconstructed trigger patch visualization for the flagged class if any.
  - **Tab "STRIP" (black-box, always runs)**: perturbation-response distribution histogram, flagged/clean split.
  - **Tab "Weight Checks"**: spectral norm ratio and activation kurtosis table per layer, flagged layers highlighted.
- **"Add findings to Assurance Report"** button, same behavior as Dataset Analysis page.

**States:** identical pattern to §2, plus an explicit `degraded` state banner when running in black-box mode: "Some checks are unavailable without white-box access. This assessment's confidence is bounded — see the report's `access_tier` field." (This exact honesty is a requirement, not a UI nicety — see PRD §3.4.)

---

## 4. Inference Batch page (`pages/3_Inference_Batch.py`)

**Precondition:** `session_state.loaded_inference_batch` set.

**Layout:**
- Summary bar: record count, signature verification rate (computed immediately on load, cheap).
- Table of records: record id, timestamp, verification status (✓/✗ badge), "View digest chain" expander per row showing the four digests + root hash.
- **"Re-verify all"** button (re-runs `provenance.verify_provenance_record` over every record — demonstrates the tamper-detection live).
- If any record fails verification: a red banner at top "N record(s) failed signature verification — possible tampering" + those rows highlighted red, each with a **"Quarantine this record"** button that writes a `PROVENANCE_TAMPERING` finding.
- **"Add findings to Assurance Report"** button.

**States:** `no_batch` → `loaded` (auto-verifies on load, no separate "run" button needed since verification is cheap and deterministic) → `verified_clean` / `verified_tampered_found`.

---

## 5. Assurance Report page (`pages/4_Assurance_Report.py`)

**Purpose:** the single-pane view judges/analysts actually read.

**Layout:**
- Big disposition badge at top: ACCEPT (green) / REVIEW (amber) / QUARANTINE (red), with the computed `risk_score` shown next to it.
- Metrics summary cards (from `metrics_summary` schema field).
- Full findings table: category, severity, confidence, reason, affected elements, disposition — sortable/filterable by severity.
- Each finding row expandable to show its full `evidence` object as formatted JSON.
- **"Download Report (.json)"** button — exact file validated against `assurance_report_schema.json`.
- **"Download Report (human-readable .pdf/.md)"** button (stretch — Phase 9; MVP can ship JSON + on-screen view only if time-limited).
- **"Sign & commit to Ledger"** button — if not already committed, writes the report to the Merkle ledger and shows the resulting `merkle_root` + a link to Audit Ledger page.
- If no report exists yet for the current session: empty state with buttons back to each analysis page ("You haven't run any analysis yet — start with Dataset, Model, or Inference Batch analysis").

**States:** `empty` → `draft` (findings collected, not yet committed to ledger) → `committed` (immutable from this point in the UI — re-running analysis creates a *new* report_id, never edits a committed one, which is itself an integrity property worth stating in the Coverage Statement).

---

## 6. Audit Ledger page (`pages/5_Audit_Ledger.py`)

**Purpose:** the tamper-evidence demo screen — this is the one to show judges live.

**Layout:**
- Table of all ledger entries: seq_index, entry_type, short payload hash, created_at, witness_export status (✓ if included in an exported checkpoint, "pending" otherwise).
- **"Verify entire chain"** button — recomputes every leaf hash and the full Merkle root, shows ✓ Valid or ✗ Broken at entry N.
- **"🔧 Simulate tampering (demo only)"** button, visibly separated/styled as a danger-zone demo tool — directly edits one entry's stored payload file on disk (bypassing the API), then prompts the user to click "Verify entire chain" again to watch it fail at the exact tampered index. This is the single most persuasive live demo moment in the whole app — it should be easy to find and easy to reset (a "Restore demo ledger" button that reloads `data/samples/demo_ledger_backup.sqlite3`).
- **"Export Checkpoint"** button — writes `reports/checkpoints/checkpoint_<timestamp>.json`, shows the file path and a reminder banner: "Copy this file to a second device or medium to complete the external-anchoring guarantee (see docs/COVERAGE_STATEMENT.md)."

**States:** `valid` (green, all checks pass) → `tampered_demo` (red, shows exactly which `seq_index` failed and why) → back to `valid` after restore.

---

## 7. Navigation map (linkage summary)

```
Home ──Load Dataset──► Dataset Analysis ──Add to report──► Assurance Report
Home ──Load Model────► Model Analysis   ──Add to report──► Assurance Report
Home ──Load Batch────► Inference Batch  ──Add to report──► Assurance Report
Assurance Report ──Sign & commit──► Audit Ledger
Audit Ledger ──Simulate tampering──► (stays on page, re-verify shows failure)
Any page ──sidebar nav──► any other page, session state persists across navigation
```

No screen is an orphan; no button leads to a dead end; every "empty state" has an explicit call-to-action back to where data gets loaded.
