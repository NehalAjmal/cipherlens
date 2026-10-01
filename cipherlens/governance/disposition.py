"""Disposition engine for CipherLens.

Computes the overall disposition for an Assurance Report using a
weighted sum of findings (no boolean AND-gates).
"""

from cipherlens.config import get_config
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def compute_overall_disposition(findings: list[Finding]) -> str:
    """Compute the overall disposition based on a weighted sum.

    Args:
        findings: List of Finding objects.

    Returns:
        "ACCEPT", "REVIEW", or "QUARANTINE".
    """
    config = get_config()
    weights = config.disposition.severity_weight
    review_thresh = config.disposition.review_threshold
    quarantine_thresh = config.disposition.quarantine_threshold
    critical_override = config.disposition.critical_override_confidence

    risk_score = 0.0

    for finding in findings:
        weight = weights.get(finding.severity, 0)
        risk_score += weight * finding.confidence

        # Force override check
        if finding.severity == "CRITICAL" and finding.confidence >= critical_override:
            logger.warning(
                "CRITICAL finding (confidence %.2f >= %.2f) forces QUARANTINE: %s",
                finding.confidence,
                critical_override,
                finding.reason,
            )
            return "QUARANTINE"

    logger.info("Total risk score: %.2f", risk_score)

    if risk_score >= quarantine_thresh:
        return "QUARANTINE"
    elif risk_score >= review_thresh:
        return "REVIEW"
    else:
        return "ACCEPT"


def annotate_finding_dispositions(findings: list[Finding]) -> None:
    """Set the disposition field for each individual finding."""
    # Simple mapping for individual findings
    for finding in findings:
        if finding.severity == "CRITICAL":
            finding.disposition = "QUARANTINE"
        elif finding.severity in {"HIGH", "MEDIUM"}:
            finding.disposition = "REVIEW"
        else:
            finding.disposition = "ACCEPT"
