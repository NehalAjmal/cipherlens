"""Shared finding representation.

Defines the Finding object used by all assessment modules, matching
BACKEND_SCHEMA.md §6 exactly.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    """A single integrity finding."""
    category: str
    severity: str
    confidence: float
    reason: str
    evidence: dict[str, Any]
    affected_elements: list[str]
    access_tier: str = "N/A"
    disposition: str = "REVIEW"
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": self.evidence,
            "affected_elements": self.affected_elements,
            "access_tier": self.access_tier,
            "disposition": self.disposition,
        }
