"""Assurance Report Builder.

Merges findings, annotates dispositions, computes the overall disposition,
and strictly validates the final report against the JSON schema.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from cipherlens.governance.disposition import annotate_finding_dispositions, compute_overall_disposition
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def _load_schema() -> dict[str, Any]:
    schema_path = Path(__file__).parent / "schema" / "assurance_report_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_report(
    findings: list[Finding],
    asset_metadata: dict[str, Any],
    metrics_summary: dict[str, Any],
    access_tier: str,
    tamper_evident_audit_record: dict[str, Any],
) -> dict[str, Any]:
    """Build and validate an Assurance Report.

    Args:
        findings: The combined list of Findings from all executed modules.
        asset_metadata: Metadata describing the dataset/model.
        metrics_summary: Top-level metrics from the modules.
        access_tier: "WHITE_BOX" or "BLACK_BOX" (from model integrity).
        tamper_evident_audit_record: The cryptographic signature binding.

    Returns:
        A validated Assurance Report dict.
    """
    annotate_finding_dispositions(findings)
    overall_disposition = compute_overall_disposition(findings)

    # Some metrics might be missing if a module degraded/failed. We must supply null
    # if the schema allows it, or a default. The schema specifies:
    # "neural_cleanse_mad_score": { "type": ["number", "null"] }, etc.
    # So we ensure keys exist.
    required_metrics = [
        "spectral_anomaly_max",
        "neural_cleanse_mad_score",
        "strip_false_positive_rate",
        "mmd_drift_statistic",
        "ks_p_value",
        "signature_verification_rate"
    ]
    for key in required_metrics:
        if key not in metrics_summary:
            metrics_summary[key] = None if key != "spectral_anomaly_max" and key != "mmd_drift_statistic" and key != "signature_verification_rate" else 0.0

    report = {
        "report_id": str(uuid.uuid4()),
        "evaluation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "asset_metadata": asset_metadata,
        "access_tier": access_tier,
        "overall_disposition": overall_disposition,
        "findings": [f.to_dict() for f in findings],
        "metrics_summary": metrics_summary,
        "tamper_evident_audit_record": tamper_evident_audit_record,
    }

    schema = _load_schema()
    try:
        jsonschema.validate(instance=report, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error("Report failed schema validation: %s", e.message)
        # In a real environment, we might want to still save the report, but for
        # MVP we should raise to ensure we know it's broken.
        raise ValueError(f"Report validation failed: {e.message}") from e

    logger.info("Successfully built and validated Assurance Report %s", report["report_id"])
    return report
