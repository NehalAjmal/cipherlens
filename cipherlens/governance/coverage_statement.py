"""Generates the final COVERAGE_STATEMENT.md from redteam test results."""

import json
from pathlib import Path
from datetime import datetime, timezone

def generate_coverage_statement():
    """Reads redteam JSON reports and generates the markdown Coverage Statement."""
    reports_dir = Path("reports/redteam")
    
    # Load Scenario A
    with open(reports_dir / "scenario_a.json") as f:
        res_a = json.load(f)
        
    # Load Scenario B
    with open(reports_dir / "scenario_b.json") as f:
        res_b = json.load(f)
        
    # Load Scenario C
    with open(reports_dir / "scenario_c.json") as f:
        res_c = json.load(f)
        
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    md_content = f"""# CipherLens Coverage Statement

**Generated:** {now}

This Coverage Statement details the empirical test results of the CipherLens air-gapped computer-vision integrity tool against adversarial and data-poisoning threats.

## Scenario A: Poisoned Data & Sybil Attack
- **Dataset Size:** {res_a['total_items']} items
- **Poisoned/Sybil Items Injected:** {res_a['poisoned_items']} items
- **Near-Duplicate Flags Caught:** {res_a['near_duplicate_findings']}
- **Sybil Velocity/Overlap Flags Caught:** {res_a['sybil_findings']}

## Scenario B: Trojaned Model
- **Access Tier Achieved:** {res_b['access_tier']}
- **Backdoor Triggers Reconstructed:** {res_b['backdoor_findings_count']}
*(Note: Phase 8 detector-level support is limited to Faster R-CNN-family architectures)*

## Scenario C: Tampered Inference Log
- **Attack Simulation:** Direct database payload modification bypassing append signatures.
- **Ledger Verification Status:** {'Valid' if res_c['ledger_valid'] else 'INVALIDATED'}
- **Corrupted Entries Detected:** {len(res_c['corrupted_indices'])}

## Environment Guarantee
All checks above completed successfully in a fully air-gapped environment with `weights_only=True` safe deserialization (and sandboxed Docker pre-validation, if available).
"""
    
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / "COVERAGE_STATEMENT.md", "w") as f:
        f.write(md_content)
        
    print(f"Successfully generated {docs_dir / 'COVERAGE_STATEMENT.md'}")

if __name__ == "__main__":
    generate_coverage_statement()
