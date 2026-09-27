# ARCHITECTURE.md — Structure Contract

This is the map. Antigravity must place every new file according to this doc. If a new file doesn't obviously belong somewhere in this tree, that's a signal to stop and ask the human before creating it (see AI_RULES.md).

---

## 1. Repository layout (full tree)

```
cipherlens/
├── README.md
├── requirements.txt
├── requirements-lock.txt
├── pyproject.toml                 # project metadata, black/ruff config, pytest config
├── .gitignore
├── .env.example                   # empty on purpose — no secrets exist in this project; kept as a documented statement of that fact
│
├── docs/                          # pushed to GitHub — judge-facing documentation, no AI-tooling mentions
│   ├── PRD.md
│   ├── TRD.md
│   ├── ARCHITECTURE.md
│   ├── APP_FLOW.md
│   ├── UI_UX_BRIEF.md
│   ├── BACKEND_SCHEMA.md
│   ├── COVERAGE_STATEMENT.md      # generated in Phase 11, from real test results
│   ├── AI_RULES.md                # ⛔ gitignored — present locally, not pushed (see .gitignore)
│   └── PLAN.md                    # ⛔ gitignored — present locally, not pushed (see .gitignore)
│
├── AGENTS.md                      # ⛔ gitignored — Antigravity's auto-loaded rules file, local only
├── .agents/workflows/*.md         # ⛔ gitignored — Antigravity slash-command workflows, local only
│
├── configs/
│   ├── default.yaml                # thresholds, paths, feature flags — see §4
│   └── redteam.yaml                # red-team scenario parameters
│
├── data/                           # gitignored except data/README.md and data/samples/ (tiny, committed fixtures)
│   ├── raw/                        # untouched COCO/YOLO input, per source
│   ├── samples/                    # small, committed, non-sensitive fixtures for tests/demo
│   └── README.md                   # how to (re)download/build the demo dataset — see HUMAN_TASKS.md
│
├── models_cache/                   # gitignored — downloaded backbone weights, demo trojaned models
│   └── README.md
│
├── reports/                        # gitignored — generated Assurance Reports, ledger DB, demo run artifacts
│   └── README.md
│
├── cipherlens/                     # the actual Python package — all import-able code lives here
│   ├── __init__.py
│   ├── pipeline.py                 # top-level orchestrator; the ONLY file allowed to call every module below
│   ├── config.py                   # loads configs/*.yaml into typed pydantic settings objects
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── coco_loader.py          # COCO JSON → DatasetItem list
│   │   ├── yolo_loader.py          # YOLO txt → DatasetItem list
│   │   ├── unified_schema.py       # DatasetItem, dataclass/pydantic model shared by both loaders
│   │   ├── model_loader.py         # safe_torch_load(), onnx loader, returns ModelHandle
│   │   └── inference_log_loader.py # JSONL → InferenceRecord list
│   │
│   ├── data_integrity/
│   │   ├── __init__.py
│   │   ├── backbone.py             # frozen reference feature extractor Φ(·)
│   │   ├── spectral_signature.py   # SVD-based trigger/backdoor anomaly scoring
│   │   ├── activation_clustering.py# false-positive reducer paired with spectral signature
│   │   ├── label_consistency.py    # k-NN label-entropy flip detector
│   │   ├── dedup.py                # perceptual hash + embedding cosine near-duplicate detector
│   │   └── aggregator.py           # sample-level → contributor-level risk score, FDR correction
│   │
│   ├── model_integrity/
│   │   ├── __init__.py
│   │   ├── neural_cleanse.py       # white-box trigger reconstruction + Anomaly Index
│   │   ├── strip.py                # black-box perturbation battery
│   │   ├── weight_checks.py        # spectral norm ratios, activation kurtosis
│   │   └── access_tier.py          # decides white-box vs black-box path, tags result with access_tier
│   │
│   ├── provenance/
│   │   ├── __init__.py
│   │   ├── crypto.py               # SHA-256 digests, Ed25519 sign/verify, canonical JSON (RFC 8785 style)
│   │   ├── merkle.py               # Merkle tree build/verify/localize-edit
│   │   └── ledger.py               # append-only SQLite-backed ledger wrapping merkle.py
│   │
│   ├── distribution_shift/
│   │   ├── __init__.py
│   │   ├── mmd.py                  # multi-scale RBF-kernel MMD (hand-rolled, see TRD.md §3.1)
│   │   ├── ks_test.py              # 2-sample KS + Wasserstein on pixel/color/DCT stats
│   │   └── energy_ood.py           # energy-based OOD score
│   │
│   ├── governance/
│   │   ├── __init__.py
│   │   ├── schema/
│   │   │   └── assurance_report_schema.json   # canonical schema, see BACKEND_SCHEMA.md
│   │   ├── report_builder.py       # assembles findings from all modules into one validated report
│   │   ├── disposition.py          # weighted risk fusion → Accept/Review/Quarantine (see AI_RULES.md: no AND-gate)
│   │   └── coverage_statement.py   # generates docs/COVERAGE_STATEMENT.md from actual test run results
│   │
│   ├── redteam/
│   │   ├── __init__.py
│   │   ├── inject_badnets.py       # Scenario A fixture generator
│   │   ├── build_trojan_model.py   # Scenario B fixture generator
│   │   └── tamper_inference.py     # Scenario C fixture generator
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── streamlit_app.py        # entrypoint: `streamlit run cipherlens/ui/streamlit_app.py`
│   │   └── pages/
│   │       ├── 1_Dataset_Analysis.py
│   │       ├── 2_Model_Analysis.py
│   │       ├── 3_Inference_Batch.py
│   │       ├── 4_Assurance_Report.py
│   │       └── 5_Audit_Ledger.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── hashing.py              # shared low-level hash helpers used by provenance + dedup
│       └── logging_config.py       # one logging setup, used everywhere, no print()
│
├── scripts/
│   ├── setup_env.sh / setup_env.ps1     # venv + pip install, one command
│   ├── download_reference_backbone.py   # one-time internet use — see HUMAN_TASKS.md
│   ├── build_wheelhouse.sh              # pip download for offline install
│   └── run_demo.py                      # scripted end-to-end demo, powers your video
│
└── tests/
    ├── unit/            # one test file per module above, mirrors the tree exactly
    ├── integration/     # cross-module: e.g. ingestion → data_integrity → governance
    └── redteam/         # Scenario A, B, C — the tests your PPT's "results" table must actually reproduce
```

**Rule:** file paths under `tests/` mirror `cipherlens/` exactly (e.g. `cipherlens/provenance/merkle.py` ↔ `tests/unit/provenance/test_merkle.py`). This makes "what's untested" visible at a glance.

---

## 2. Module boundaries — who is allowed to call whom

```
ingestion/            ──► produces: DatasetItem, ModelHandle, InferenceRecord (unified_schema.py)
                            │
                            ▼
data_integrity/        model_integrity/        distribution_shift/     provenance/
      │                       │                        │                   │
      └───────────────────────┴────────────┬───────────┘                   │
                                            ▼                               │
                                     governance/                            │
                                  (report_builder,                          │
                                   disposition,                             │
                                   coverage_statement)  ◄────────────────────┘
                                            │
                                            ▼
                                          ui/
```

**Hard rules (enforced by code review / AI_RULES.md, not just convention):**
1. `data_integrity/`, `model_integrity/`, `distribution_shift/`, and `provenance/` **never import from each other.** Each is independently testable and independently degradable (if one module errors, the others still produce findings).
2. Only `pipeline.py` and `governance/report_builder.py` are allowed to import from more than one of the above four packages.
3. `ui/` never contains business logic — every Streamlit page calls into `pipeline.py` or `governance/` and only handles rendering/session state. If a page file is doing math, that math belongs in a module and got misplaced.
4. `redteam/` may import from `ingestion/` (to build fixtures) but nothing in `cipherlens/` (outside `tests/` and `scripts/`) may import from `redteam/` — red-team fixture generation is test/demo tooling, not production code.
5. No module reaches across to read another module's config directly — everything goes through `config.py`'s typed settings object, passed in as a function argument. No global mutable state.

---

## 3. Data flow (runtime)

```
1. Human/UI selects a dataset dir, model file, and/or inference JSONL.
2. ingestion/* normalizes into DatasetItem / ModelHandle / InferenceRecord.
3. pipeline.py fans out to the three assessment modules IN PARALLEL (or sequentially on
   low-resource machines — config flag `execution.parallel: true|false`):
     - data_integrity.analyze(dataset_items, config) -> DataIntegrityFindings
     - model_integrity.analyze(model_handle, access_tier, config) -> ModelIntegrityFindings
     - distribution_shift.analyze(dataset_items, reference_stats, config) -> ShiftFindings
4. For each inference record processed, provenance.generate_provenance_record(...) is called
   at the moment of inference (or replayed against existing logs in batch mode).
5. governance.report_builder.build(findings...) merges everything into ONE
   assurance_report_schema.json-validated dict.
6. governance.disposition.decide(report) assigns Accept / Review / Quarantine using WEIGHTED
   RISK FUSION (never a simple AND-gate — see AI_RULES.md, this was an explicitly fixed bug
   in your PPT's own feasibility slide, don't reintroduce it).
7. governance's report + a hash of it is appended to provenance/ledger.py's Merkle chain.
8. ui/ reads reports/ + the ledger DB and renders. UI never re-computes findings — it only
   displays what pipeline.py already produced and persisted.
```

---

## 4. Configuration — one place for every number

All thresholds (spectral signature IQR multiplier, Neural Cleanse Anomaly Index cutoff, MMD kernel bandwidths, dedup cosine-distance cutoff, disposition weights, etc.) live in `configs/default.yaml`, never hardcoded inline in a module. `config.py` loads this into a typed object (pydantic `BaseSettings`) that every module receives as a parameter. This means: (a) tuning a threshold never means hunting through files, (b) every run can log exactly which config version produced which report (put the config hash in the Assurance Report's `asset_metadata`), (c) Antigravity can be told "only touch `configs/default.yaml`" for a tuning task without touching any module code.

---

## 5. Naming & style conventions
- Python: `snake_case` for functions/files, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants.
- One class or one tightly-related group of functions per file. No file should exceed ~300 lines — if it does, that's a signal the module needs splitting (open a new file in the same package, not a monolith).
- Every public function has a docstring (purpose, args, returns) and full type hints. No bare `def analyze(x):`.
- No `print()` anywhere in `cipherlens/` — use `utils/logging_config.py`'s logger.
- No bare `except:` — catch specific exceptions, log them, and either re-raise or return a typed error result. Never swallow silently (see AI_RULES.md).
- Imports: standard library, then third-party, then local — each group alphabetized, separated by a blank line (this is what `ruff`/`isort` enforce automatically; configured once in `pyproject.toml`).

---

## 6. Why this structure (so nobody "simplifies" it back into spaghetti)
The four assessment modules being import-isolated from each other is the single most important structural decision in this project — it's what makes "graceful degradation" (a hard requirement in your PRD) actually true in code, not just true in a slide. If `model_integrity` could reach into `data_integrity`'s internals, a bug in one would silently break the other, and you could no longer honestly report "black-box assessment unavailable, here's why" without the whole pipeline crashing.