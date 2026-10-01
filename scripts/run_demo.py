#!/usr/bin/env python3
"""
Headless runner for the CipherLens demo.
Executes the full pipeline against data/samples/ and commits to the ledger.
"""

import sys
import time
from pathlib import Path
import json

root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from cipherlens.pipeline import run_pipeline

def main():
    print("="*60)
    print("CipherLens Headless Demo Runner")
    print("="*60)
    
    print("\n[1/4] Initializing environment...")
    dataset_path = root_path / "data/samples/annotations/instances_samples.json"
    images_dir = root_path / "data/samples/images"
    model_path = root_path / "data/samples/resnet50_clean.onnx"
    
    if not dataset_path.exists() or not model_path.exists():
        print("ERROR: Sample data not found. Please run scripts/download_demo_data.py and scripts/download_resnet_onnx.py first.")
        sys.exit(1)
        
    print(f"Dataset: {dataset_path}")
    print(f"Model:   {model_path}")
    
    print("\n[2/4] Executing Pipeline (Data & Model Integrity)...")
    start_time = time.time()
    
    report = run_pipeline(
        dataset_path=str(dataset_path),
        images_dir=str(images_dir),
        dataset_format="COCO",
        model_path=str(model_path),
        model_format="ONNX"
    )
    
    elapsed = time.time() - start_time
    print(f"\nPipeline finished in {elapsed:.1f} seconds.")
    
    print("\n[3/4] Assurance Report Summary:")
    print(f"  Report ID:   {report['report_id']}")
    print(f"  Asset Type:  {report['asset_metadata']['asset_type']}")
    print(f"  Disposition: {report['overall_disposition']}")
    from cipherlens.governance.disposition import compute_risk_score
    from cipherlens.utils.finding import Finding
    
    findings_objs = [Finding(**f) for f in report['findings']]
    risk_score = compute_risk_score(findings_objs)
    
    print(f"  Risk Score:  {risk_score:.2f}")
    
    print("\n  Top Findings:")
    for f in report['findings'][:3]:
        print(f"    - [{f['severity']}] {f['category']} (confidence: {f['confidence']:.2f}): {f['reason']}")
    if len(report['findings']) > 3:
        print(f"    ... and {len(report['findings']) - 3} more.")
        
    print("\n[4/4] Output saved:")
    print("  Report committed to reports/ledger.sqlite3")
    
    # Save a JSON copy for the user to inspect easily
    out_file = root_path / f"reports/demo_report_{report['report_id'][:8]}.json"
    out_file.parent.mkdir(exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  JSON copy saved to {out_file.relative_to(root_path)}")
    
    print("\nDemo complete! Start the UI via `streamlit run cipherlens/ui/streamlit_app.py` to view the Audit Ledger.")
    print("="*60)

if __name__ == "__main__":
    main()
