# TRD.md — Technical Requirements Document

Exact stack. No "pick an appropriate framework." Every line item is free.

---

## 1. Languages & runtime

| Item | Choice | Why |
|---|---|---|
| Language | **Python 3.11** (3.10–3.12 also fine) | Every required library (ART, alibi-detect, onnxruntime, cryptography, Streamlit) has mature Python support; matches the Gemini design doc and your PPT tech stack exactly. |
| Package manager | **pip + venv** (stdlib `venv`, no Poetry/Conda required, though Conda is fine if you already use it) | Zero extra tooling to install; free. |
| OS support | Windows 10+, macOS 12+, Linux (any recent distro) | Pure-Python + cross-platform C-extension wheels for all deps below. |
| Hardware | CPU-only baseline. No GPU required. 8 GB RAM comfortable minimum. ~1 GB free disk for backbone + demo dataset + venv. | Verified against library requirements in §2. |

---

## 2. Libraries — exact list, versions, role, and free-ness audit

All installed via `pip install -r requirements.txt` from **PyPI**, which is free and requires no account or API key. Internet is needed once, at install time, then never again at run time (per PRD §3.4).

| Library | Min version | Role | License / cost |
|---|---|---|---|
| `torch`, `torchvision` | ≥2.2.0 | Load PyTorch/TorchScript models; frozen backbone (ResNet‑18/MobileNetV3) for embeddings; Neural Cleanse gradient optimization. CPU wheel only — do **not** install the CUDA build. | BSD — free, no account needed. |
| `onnxruntime` | ≥1.18.0 | Load and run `.onnx` models offline. | MIT — free. |
| `onnx` | ≥1.15.0 | Graph inspection without executing arbitrary code. | Apache‑2.0 — free. |
| `adversarial-robustness-toolbox` (`art`) | ≥1.17.0 | Spectral Signature defense, Activation Clustering, Neural Cleanse-style trigger reconstruction. | MIT — free. |
| `alibi-detect` | ≥0.12.0 | MMD and KS drift detectors (optional — see §3 note on a lighter custom alternative). | Apache‑2.0 — free, fully offline once installed. |
| `scikit-learn` | ≥1.4.0 | k‑NN, clustering, general stats utilities. | BSD — free. |
| `scipy` | ≥1.11.0 | KS test, Wasserstein distance, MAD. | BSD — free. |
| `numpy` | ≥1.26.0 | Array math throughout. | BSD — free. |
| `opencv-python-headless` | ≥4.9.0 | Pixel ops, EXIF, 2D‑FFT for high-frequency spectral checks. | Apache‑2.0/BSD — free. |
| `ImageHash` | ≥4.3.1 | Perceptual hashing (dHash) for near-duplicate detection. | BSD — free. |
| `cryptography` | ≥42.0.0 | Ed25519 keygen/sign/verify, SHA‑256. | Apache‑2.0/BSD — free. |
| `streamlit` | ≥1.32.0 | Offline analyst dashboard. | Apache‑2.0 — free; **do not** use Streamlit Community Cloud hosting (that's a network dependency) — run `streamlit run` locally only. |
| `jsonschema` | ≥4.21.0 | Validate every Assurance Report against `assurance_report_schema.json`. | MIT — free. |
| `pytest` | ≥8.0.0 | All unit/integration/red-team tests. | MIT — free. |
| `pydantic` | ≥2.6.0 | Typed report/config models, cleaner than hand-rolled dict validation. | MIT — free. |
| `pillow` | ≥10.0.0 | Image I/O support library (dependency of several of the above; pinned explicitly for reproducibility). | HPND — free. |

**Intentionally dropped from the Gemini design doc, with reasons (documented here so nobody re-adds them by accident):**
- `pyarrow` + Plasma shared-memory store, Unix-domain-socket orchestrator, LMDB — over-engineered for a single-machine hackathon build. Replaced with plain local files + SQLite (stdlib `sqlite3`, already free and installed) for the ledger, and in-process function calls instead of an IPC layer. If judges specifically want to see the shared-memory design, it's a documented stretch item, not a blocker.
- Plotly/Bokeh — Streamlit's built-in charting (backed by Altair, bundled) covers everything the MVP dashboard needs; fewer dependencies, less to break.

**No dependency in this project ever requires:** a paid tier, an API key, a cloud account, a credit card, or a subscription. If a future idea would require one, it doesn't go in — full stop, per PRD §4.

---

## 3. Design notes on two specific technical choices

### 3.1 MMD/KS — `alibi-detect` vs. a custom implementation
`alibi-detect`'s MMD/KS drift detectors are solid and free, but pull in a backend (PyTorch, which you already have) and add install weight. For MVP speed and fewer moving parts, **Phase 5 implements MMD and KS by hand** using `numpy`/`scipy` (the exact formulas are in the Gemini design doc and repeated in PLAN.md Phase 5) — this is genuinely not hard (a multi-scale RBF kernel MMD is ~20 lines of numpy) and keeps the dependency surface small. `alibi-detect` stays in `requirements.txt` as an **optional, swappable backend** behind the same interface, for teams that want to cite a published library by name in their report. Both are free either way.

### 3.2 Neural Cleanse / STRIP scope
ART's built-in Neural Cleanse-style defenses and STRIP-style input filtering target **classification models** (they optimize/patch against a single predicted label). Since your pipeline's real assets are object detectors, MVP Phase 4 runs these against:
1. A frozen or lightly fine-tuned classification backbone (stands in for "model integrity check on a supplied model," which is valid — many vendor-supplied CV backbones *are* classifiers or have a classification head), and
2. A classifier trained on **cropped detection outputs** (crop each bbox, classify the crop) as a bridge toward detector-level coverage.

The genuine detector-level extension (patching Neural Cleanse's loss to attack a detector's objectness + class + box-regression heads jointly) is Phase 8, marked stretch/research-risk in PLAN.md, exactly matching your own slide's "pending" note.

---

## 4. Tooling around the code (also all free)

| Tool | Purpose | Cost |
|---|---|---|
| **Google Antigravity** | Agentic IDE, the "vibe coding" surface. | Free tier (Gemini-API-quota based). See HUMAN_TASKS.md for the one thing to check on sign-in. |
| **Git + GitHub** | Version control, the repo you submit. | Free (public repo, or free private repos under a personal/education account). |
| **VS Code** (Antigravity is a VS Code fork, so this is effectively bundled) | Manual code review when you want to read without the agent. | Free. |
| **GitHub Actions** (optional, stretch) | CI to run `pytest` on push. | Free tier (2,000 min/month on public repos, generous free minutes on private too). |

---

## 5. Version pinning strategy
`requirements.txt` — loose minimums, for day-to-day development.
`requirements-lock.txt` — exact pinned versions, generated once your stack is stable (`pip freeze > requirements-lock.txt`), used to build the "offline wheelhouse" your PPT promises (`pip download -r requirements-lock.txt -d wheelhouse/` while online once, then `pip install --no-index --find-links=wheelhouse/ -r requirements-lock.txt` on the air-gapped demo machine). Exact commands are in HUMAN_TASKS.md.
