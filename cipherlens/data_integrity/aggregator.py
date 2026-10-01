"""Data Integrity Aggregator.

Runs all data integrity checks and aggregates findings, including
contributor-level risk aggregation.
"""

from cipherlens.data_integrity.activation_clustering import check_activation_clustering
from cipherlens.data_integrity.dedup import check_duplicates
from cipherlens.data_integrity.label_consistency import check_label_consistency
from cipherlens.data_integrity.spectral_signature import check_spectral_signatures
from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_data_integrity_checks(dataset_items: list[DatasetItem], images_dir: str) -> list[Finding]:
    """Execute all data integrity modules and return aggregated findings.

    Args:
        dataset_items: List of DatasetItem instances.
        images_dir: Base directory for the images.

    Returns:
        A list of unified Finding objects.
    """
    findings: list[Finding] = []

    logger.info("Running Spectral Signatures...")
    findings.extend(check_spectral_signatures(dataset_items, images_dir))
    
    logger.info("Running Activation Clustering...")
    findings.extend(check_activation_clustering(dataset_items, images_dir))
    
    logger.info("Running Label Consistency...")
    findings.extend(check_label_consistency(dataset_items, images_dir))
    
    logger.info("Running Deduplication...")
    findings.extend(check_duplicates(dataset_items, images_dir))
    
    # Contributor-level aggregation
    # If a specific contributor is involved in multiple HIGH/CRITICAL findings,
    # emit a contributor-level finding.
    contributor_flags = {}
    
    # Map item_id to contributor
    item_to_contributor = {item.item_id: item.contributor_id for item in dataset_items}
    
    for f in findings:
        if f.severity in ("HIGH", "CRITICAL"):
            for element_id in f.affected_elements:
                contrib = item_to_contributor.get(element_id)
                if contrib:
                    contributor_flags[contrib] = contributor_flags.get(contrib, 0) + 1
                    
    for contrib, flag_count in contributor_flags.items():
        if flag_count >= 3:
            # Emit a contributor risk finding
            findings.append(
                Finding(
                    category="DATA_POISONING",
                    severity="CRITICAL",
                    confidence=0.9,
                    reason=f"Contributor '{contrib}' is associated with {flag_count} high-severity integrity violations.",
                    evidence={"flag_count": flag_count, "contributor_id": contrib},
                    affected_elements=[contrib],
                )
            )

    logger.info("Running Sybil Identity Heuristics...")
    from cipherlens.data_integrity.sybil import check_sybil_heuristics
    sybil_findings = check_sybil_heuristics(dataset_items, findings)
    findings.extend(sybil_findings)

    return findings
