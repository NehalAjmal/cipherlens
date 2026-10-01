"""Sybil Resistance / Contributor Identity Heuristics.

Provides statistical extensions to contributor risk aggregation based on:
1. Cross-contributor near-duplicate overlaps.
2. Submission velocity anomalies.
"""

from collections import defaultdict
from datetime import datetime

from cipherlens.ingestion.unified_schema import DatasetItem
from cipherlens.utils.finding import Finding
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


def check_sybil_heuristics(
    dataset_items: list[DatasetItem], 
    existing_findings: list[Finding]
) -> list[Finding]:
    """Execute Sybil heuristics to flag potential fake/automated identities.
    
    Args:
        dataset_items: The list of items in the batch.
        existing_findings: Findings from previous modules (e.g., Deduplication).
        
    Returns:
        A list of new Findings in the SYBIL_RISK category.
    """
    sybil_findings: list[Finding] = []
    
    # Pre-compute mapping of item_id -> contributor_id
    item_to_contrib = {item.item_id: item.contributor_id for item in dataset_items}
    
    # ---------------------------------------------------------
    # 1. Cross-Contributor Near-Duplicate Overlap
    # ---------------------------------------------------------
    cross_contrib_dupe_pairs = []
    for f in existing_findings:
        if f.category == "NEAR_DUPLICATE" and len(f.affected_elements) == 2:
            id1, id2 = f.affected_elements
            c1 = item_to_contrib.get(id1)
            c2 = item_to_contrib.get(id2)
            if c1 and c2 and c1 != c2:
                cross_contrib_dupe_pairs.append((c1, c2, id1, id2))
                
    if cross_contrib_dupe_pairs:
        # Group by the contributor pairs to measure the scale
        pair_counts = defaultdict(list)
        for c1, c2, id1, id2 in cross_contrib_dupe_pairs:
            # Sort to make pair undirected
            pair = tuple(sorted([c1, c2]))
            pair_counts[pair].append((id1, id2))
            
        for (c1, c2), items in pair_counts.items():
            sybil_findings.append(
                Finding(
                    category="SYBIL_RISK",
                    severity="HIGH",
                    confidence=0.85, # Strong signal of coordinated/sybil accounts
                    reason=f"Cross-contributor duplicate overlap: '{c1}' and '{c2}' submitted {len(items)} near-identical items.",
                    evidence={
                        "contributor_1": c1,
                        "contributor_2": c2,
                        "overlap_count": len(items),
                        "overlapping_items": items
                    },
                    affected_elements=[c1, c2]
                )
            )

    # ---------------------------------------------------------
    # 2. Submission Velocity Anomalies
    # ---------------------------------------------------------
    contrib_timestamps = defaultdict(list)
    for item in dataset_items:
        ts_str = item.acquisition_meta.timestamp if item.acquisition_meta else None
        if ts_str:
            try:
                # Parse standard ISO format
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                contrib_timestamps[item.contributor_id].append(ts)
            except ValueError:
                pass
                
    for contrib, timestamps in contrib_timestamps.items():
        if len(timestamps) >= 10:
            timestamps.sort()
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            
            # If > 10 items were created/submitted within a 1-second window, it's highly anomalous
            if duration <= 1.0:
                sybil_findings.append(
                    Finding(
                        category="SYBIL_RISK",
                        severity="MEDIUM",
                        confidence=0.75,
                        reason=f"Velocity anomaly: '{contrib}' submitted {len(timestamps)} items within {duration:.1f} seconds.",
                        evidence={
                            "contributor_id": contrib,
                            "item_count": len(timestamps),
                            "duration_seconds": duration,
                            "first_seen": timestamps[0].isoformat(),
                            "last_seen": timestamps[-1].isoformat()
                        },
                        affected_elements=[contrib]
                    )
                )

    if sybil_findings:
        logger.info("Flagged %d SYBIL_RISK findings.", len(sybil_findings))

    return sybil_findings
