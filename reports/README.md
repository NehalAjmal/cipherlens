# reports/

Generated CipherLens output artifacts.

## Structure

- `assurance/<report_id>.json` — Assurance Reports validated against `assurance_report_schema.json`.
- `provenance/<batch_id>.jsonl` — Per-inference provenance records.
- `checkpoints/checkpoint_<timestamp>.json` — Signed Merkle ledger checkpoints.
- `ledger.sqlite3` — Append-only audit ledger (SQLite).

**This directory is gitignored.** Contents are regenerated per run.
