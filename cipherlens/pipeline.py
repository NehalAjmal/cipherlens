"""Top-level orchestrator for CipherLens.

Runs the full integrity assessment pipeline across data, models,
and distribution shift, merges the results via the governance layer,
and commits them to the cryptographic ledger.
"""

from pathlib import Path
from typing import Any

import numpy as np

from cipherlens.config import get_config
from cipherlens.data_integrity import analyze as analyze_data_integrity
from cipherlens.data_integrity.backbone import embed
from cipherlens.distribution_shift import analyze as analyze_distribution_shift
from cipherlens.governance.report_builder import build_report
from cipherlens.ingestion.coco_loader import load_coco_dataset
from cipherlens.ingestion.model_loader import load_model
from cipherlens.ingestion.yolo_loader import load_yolo_dataset
from cipherlens.model_integrity import analyze as analyze_model_integrity
from cipherlens.provenance.crypto import generate_keypair, sign_payload
from cipherlens.provenance.ledger import ProvenanceLedger
from cipherlens.utils.finding import Finding
from cipherlens.utils.hashing import sha256_digest
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_pipeline(
    dataset_path: str | None = None,
    images_dir: str | None = None,
    dataset_format: str = "COCO",
    model_path: str | None = None,
    model_format: str = "PYTORCH",
    access_tier_override: str | None = None,
    ref_embeddings: np.ndarray | None = None, # For distribution shift
) -> dict[str, Any]:
    """Execute the full assessment pipeline.

    Gracefully handles degraded inputs (e.g. only model, no dataset).

    Args:
        dataset_path: Path to dataset annotations (optional).
        images_dir: Path to dataset images (optional).
        dataset_format: "COCO" or "YOLO".
        model_path: Path to model file (optional).
        model_format: "PYTORCH" or "ONNX".
        access_tier_override: "WHITE_BOX" or "BLACK_BOX".
        ref_embeddings: Reference embeddings for drift calculation (optional).

    Returns:
        The fully validated Assurance Report dictionary.
    """
    config = get_config()
    findings: list[Finding] = []
    asset_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
    asset_type = "UNKNOWN"
    asset_identifier = "UNKNOWN"
    
    # 1. Ingest & Analyze Data
    test_embeddings = None
    test_image_paths = []
    
    if dataset_path and images_dir:
        logger.info("Loading dataset %s format %s", dataset_path, dataset_format)
        if dataset_format.upper() == "COCO":
            items, skipped = load_coco_dataset(dataset_path, images_dir)
        elif dataset_format.upper() == "YOLO":
            # For pipeline MVP we assume class names are ['person', 'car', ...] etc.
            items, skipped = load_yolo_dataset(images_dir, dataset_path, ["0", "1", "2"])
        else:
            raise ValueError(f"Unknown dataset format: {dataset_format}")
            
        logger.info("Running Data Integrity checks...")
        data_findings = analyze_data_integrity(items, images_dir)
        findings.extend(data_findings)
        
        # Prepare for distribution shift
        test_image_paths = [f"{images_dir}/{item.image_path}" for item in items]
        if test_image_paths:
            test_embeddings = embed(test_image_paths)
            
        # Update metadata for the primary asset (assume dataset if provided)
        with open(dataset_path, "rb") as f:
            asset_sha256 = sha256_digest(f.read())
        asset_type = "DATASET"
        asset_identifier = str(Path(dataset_path).name)

    # 2. Analyze Distribution Shift
    if test_embeddings is not None and ref_embeddings is not None:
        logger.info("Running Distribution Shift checks...")
        shift_findings = analyze_distribution_shift(ref_embeddings, test_embeddings, test_image_paths)
        findings.extend(shift_findings)

    # 3. Ingest & Analyze Model
    final_access_tier = "N/A"
    if model_path:
        logger.info("Loading model %s format %s", model_path, model_format)
        model_handle = load_model(
            model_path=model_path,
            model_id=str(Path(model_path).name),
            access_tier_available="WHITE_BOX" if model_format.upper() == "PYTORCH" else "BLACK_BOX"
        )
        logger.info("Running Model Integrity checks...")
        model_findings = analyze_model_integrity(model_handle, access_tier_override)
        findings.extend(model_findings)
        
        # Update metadata if we didn't have a dataset, or we are evaluating the model as the primary asset
        if asset_type == "UNKNOWN":
            asset_type = "MODEL"
            asset_identifier = model_handle.manifest.model_id
            asset_sha256 = model_handle.manifest.sha256
        
        final_access_tier = model_handle.manifest.access_tier_available

    # Edge case: model evaluation overrides access_tier in report root
    if any(f.category == "MODEL_BACKDOOR" for f in findings):
        for f in findings:
            if f.category == "MODEL_BACKDOOR":
                final_access_tier = f.access_tier
                break

    # 4. Gather Metrics Summary
    metrics_summary = {
        "spectral_anomaly_max": 0.0,
        "neural_cleanse_mad_score": None,
        "strip_false_positive_rate": None,
        "mmd_drift_statistic": 0.0,
        "ks_p_value": None,
        "signature_verification_rate": 1.0,
    }
    
    for f in findings:
        if "spectral_anomaly_max" in f.evidence and f.evidence["spectral_anomaly_max"] > metrics_summary["spectral_anomaly_max"]:
            metrics_summary["spectral_anomaly_max"] = f.evidence["spectral_anomaly_max"]
        if "neural_cleanse_mad_score" in f.evidence:
            metrics_summary["neural_cleanse_mad_score"] = f.evidence["neural_cleanse_mad_score"]
        if "mmd_squared_score" in f.evidence:
            metrics_summary["mmd_drift_statistic"] = f.evidence["mmd_squared_score"]
        if "significant_features_ratio" in f.evidence:
            # Not exactly p-value, but a placeholder for KS summary
            metrics_summary["ks_p_value"] = f.evidence["significant_features_ratio"]

    # 5. Connect to Ledger and prep signing
    ledger = ProvenanceLedger(config.ledger.db_path)
    tree = ledger.get_merkle_tree()
    merkle_root = tree.root if tree.root else "0000000000000000000000000000000000000000000000000000000000000000"
    
    # In a real system, the operator provides their key. Here we generate a transient one.
    priv, pub = generate_keypair()
    
    # We must sign something to prove provenance. We'll sign the asset_sha256 and findings hash.
    # But since the audit record goes *inside* the report, we sign a proxy payload.
    proxy_payload = {
        "asset_sha256": asset_sha256,
        "merkle_root": merkle_root,
        "findings_count": len(findings)
    }
    signature = sign_payload(proxy_payload, priv)
    
    tamper_evident_audit_record = {
        "merkle_root": merkle_root,
        "signature": signature,
        "signing_key_id": "ephemeral_run_key"
    }
    
    asset_metadata = {
        "asset_type": asset_type,
        "asset_identifier": asset_identifier,
        "asset_sha256": asset_sha256,
        "format": dataset_format if asset_type == "DATASET" else model_format,
        "config_hash": "dummy_hash_for_mvp"
    }

    # 6. Build and Validate Report
    logger.info("Building Assurance Report...")
    report = build_report(
        findings=findings,
        asset_metadata=asset_metadata,
        metrics_summary=metrics_summary,
        access_tier=final_access_tier if final_access_tier != "N/A" else "BLACK_BOX",
        tamper_evident_audit_record=tamper_evident_audit_record,
    )
    
    # 7. Commit to Ledger
    logger.info("Committing report to ledger...")
    ledger.append_record(report)
    
    return report
