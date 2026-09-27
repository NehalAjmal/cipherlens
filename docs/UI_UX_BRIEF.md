# UI_UX_BRIEF.md — Look and Feel

Streamlit constrains layout somewhat (this is intentional — it's free, fast to build, and judges care about function over pixel-perfect design). Within that constraint, here is the exact visual language, matching your existing PPT branding so the demo and the deck feel like one product.

---

## 1. Brand basis (pulled directly from your PPT)
- Primary dark: **navy blue** (`#1F3864` / similar) — headers, primary buttons, sidebar background.
- Alert red: **`#C00000`**-ish — CRITICAL severity, QUARANTINE badge, tampering banners.
- Alert amber: **`#BF8F00`**-ish — MEDIUM severity, REVIEW badge.
- Success green: **`#548235`**-ish — LOW/INFO severity, ACCEPT badge, verified checkmarks.
- Neutral background: white/light gray for content area, dark navy sidebar (Streamlit's native dark sidebar works here with a custom `.streamlit/config.toml` theme — see §5).
- This is the same "risk tier" color language already on your Technical Approach slide (Normal/Moderate/Critical dots) — reuse it exactly so the deck and the live demo visually match.

---

## 2. Typography
- Streamlit's default sans-serif (system font stack) is fine — do not fight the framework by injecting custom web fonts (adds a network dependency risk and fragility, contradicts the offline claim if a font CDN is used; if a custom font is wanted, self-host the font file locally, don't link to Google Fonts).
- Headers: bold, navy. Body: default weight, dark gray (`#262730`, Streamlit's default). Monospace (`st.code`) for hashes, digests, and JSON — always truncate long hashes visually (`abcd1234…ef567890`) with a "copy full value" affordance, never wrap a 64-char hex string across lines.

---

## 3. Layout principles
- **Sidebar = navigation + session state.** Main area = content. Never put primary actions in the sidebar except navigation.
- **Cards over walls of text.** Use `st.container(border=True)` for each logical block (summary bar, each analysis tab's content, each finding).
- **Tables over prose** for findings — analysts scan tables, they don't read paragraphs. Use `st.dataframe` with column config (not raw `st.write(df)`), sortable, with severity as a colored badge column (use a small emoji or colored text, e.g. 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW / ⚪ INFO — this also works if the deployment's theme doesn't render custom CSS well).
- **Every number is traceable.** Any metric shown (risk score, MMD statistic, anomaly index) must be one click away from the raw evidence that produced it (an expander showing the `evidence` JSON) — never show a bare number with no drill-down. This is the product's whole value proposition (evidence-based, not a black-box stamp) and the UI must embody it, not just the copy.

---

## 4. Empty / loading / error states (apply uniformly across all 5 analysis pages)
- **Empty:** friendly icon + one sentence + a clear single call-to-action button. Never a blank page.
- **Loading:** `st.spinner` with a text label that updates per pipeline stage (not a generic "Loading..." — see APP_FLOW.md §2 for the exact stage labels). For anything over ~2 seconds, a `st.progress` bar with stage count is preferred over a spinner.
- **Error:** `st.error()` with the *specific* exception message and, where possible, a one-line suggested fix (e.g., "No `labels/` folder found — CipherLens expects YOLO datasets in the standard `images/` + `labels/` layout. See docs/BACKEND_SCHEMA.md §2."). Never a bare traceback dumped to the user — log the traceback via `utils/logging_config.py`, show the human-readable summary in the UI.
- **Partial/degraded success** (e.g., black-box-only model, or one module errored while others succeeded): amber `st.warning()` banner explaining exactly what's missing and why, not hidden, not a silent gap.

---

## 5. Streamlit theming (concrete config, not vague guidance)

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1F3864"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfOutput = false
```
This file ships in the repo root so the theme is automatic on `streamlit run` — no manual per-machine setup.

---

## 6. Accessibility & practicality
- Never rely on color alone for severity — always pair color with the text label (CRITICAL/HIGH/etc.) and/or emoji, per §3.
- Every button has a clear, action-verb label ("Run Data Integrity Analysis," not "Go" or "Submit").
- Keep the demo dataset small enough that every analysis completes in under ~10 seconds on a judge's laptop — a slow spinner during a live demo is worse than a slightly smaller dataset. (This is a UX decision with an engineering consequence — flag it back to HUMAN_TASKS.md's dataset-size guidance.)
- The "Simulate tampering" and "Restore demo ledger" buttons (Audit Ledger page) are the single highest-leverage 30 seconds of any live demo — they should be visually prominent, not buried in an expander.

---

## 7. What NOT to do
- No custom React/JS injection into Streamlit (fragile, offline-risk if it pulls any CDN asset, and outside the agreed stack in TRD.md).
- No infinite-scroll or pagination gimmicks — this is an analyst tool for hundreds of records, not a consumer feed; a plain sortable/filterable table is correct and faster to build.
- No animation for animation's sake — motion is fine only where it communicates state change (e.g., a checkmark animating in after successful verification is fine; a decorative background particle effect is not, and it's also the kind of thing that eats build time you don't have).
