"""Unit tests for the Data Integrity module.

Uses small, hand-checkable synthetic fixtures to verify detection algorithms.
"""

import numpy as np
import pytest

from cipherlens.data_integrity.activation_clustering import check_activation_clustering
from cipherlens.data_integrity.aggregator import run_data_integrity_checks
from cipherlens.data_integrity.dedup import check_duplicates
from cipherlens.data_integrity.label_consistency import check_label_consistency
from cipherlens.data_integrity.spectral_signature import check_spectral_signatures
from cipherlens.ingestion.unified_schema import Annotation, DatasetItem, AcquisitionMeta


def _mock_dataset_items(count: int, class_name: str = "person") -> list[DatasetItem]:
    return [
        DatasetItem(
            item_id=f"item_{i}",
            image_path=f"img_{i}.jpg",
            image_sha256=f"hash_{i}",
            width=100,
            height=100,
            annotations=[Annotation(category_id=1, category_name=class_name, bbox_xywh=[0, 0, 10, 10])],
            contributor_id="contributor_1",
            batch_id="b1",
            source_format="TEST",
            acquisition_meta=AcquisitionMeta(),
        )
        for i in range(count)
    ]


def test_label_consistency():
    """Verify that identical hashes with mismatched labels flag a LABEL_FLIP."""
    items = _mock_dataset_items(2)
    # Force identical hashes but different labels
    items[0].image_sha256 = "same_hash"
    items[1].image_sha256 = "same_hash"
    
    items[0].annotations[0].category_name = "cat"
    items[1].annotations[0].category_name = "dog"
    
    findings = check_label_consistency(items, "/dummy")
    assert len(findings) == 1
    assert findings[0].category == "LABEL_FLIP"
    assert "item_0" in findings[0].affected_elements
    assert "item_1" in findings[0].affected_elements


def test_spectral_signature_outlier(monkeypatch):
    """Verify spectral signature detects an outlier using mock embeddings."""
    items = _mock_dataset_items(5)
    
    # Create 5 embeddings: 4 normal, 1 extreme outlier
    embeddings = np.array([
        [0.1, 0.1],
        [0.12, 0.08],
        [0.08, 0.12],
        [0.11, 0.09],
        [10.0, -10.0],  # Outlier
    ])
    
    # Mock the embed function so it doesn't try to load images/backbone
    monkeypatch.setattr("cipherlens.data_integrity.spectral_signature.embed", lambda paths: embeddings)
    
    findings = check_spectral_signatures(items, "/dummy")
    assert len(findings) == 1
    assert findings[0].category == "DATA_POISONING"
    assert "item_4" in findings[0].affected_elements


def test_activation_clustering(monkeypatch):
    """Verify activation clustering detects a minority cluster."""
    items = _mock_dataset_items(10)
    
    # Create embeddings: 8 in one cluster, 2 in another (minority < 35%)
    embeddings = np.array([
        [0.1, 0.1], [0.1, 0.1], [0.1, 0.1], [0.1, 0.1],
        [0.1, 0.1], [0.1, 0.1], [0.1, 0.1], [0.1, 0.1],
        [5.0, 5.0], [5.0, 5.0]  # Anomalous cluster
    ])
    
    monkeypatch.setattr("cipherlens.data_integrity.activation_clustering.embed", lambda paths: embeddings)
    
    findings = check_activation_clustering(items, "/dummy")
    assert len(findings) == 1
    assert findings[0].category == "DATA_POISONING"
    assert len(findings[0].affected_elements) == 2


def test_dedup_cosine(monkeypatch):
    """Verify duplicate detection finds similar embeddings."""
    items = _mock_dataset_items(2)
    
    # 2 identical embeddings
    embeddings = np.array([
        [1.0, 0.0],
        [1.0, 0.001],
    ])
    
    monkeypatch.setattr("cipherlens.data_integrity.dedup.embed", lambda paths: embeddings)
    
    findings = check_duplicates(items, "/dummy")
    assert len(findings) == 1
    assert findings[0].category == "NEAR_DUPLICATE"
    assert "item_0" in findings[0].affected_elements
    assert "item_1" in findings[0].affected_elements


def test_contributor_aggregation(monkeypatch):
    """Verify the aggregator emits a CRITICAL finding if a contributor has >= 3 flags."""
    items = _mock_dataset_items(3)
    
    def mock_checks(items, path):
        return [
            # 3 HIGH findings for the same contributor (contributor_1)
            type("Finding", (), {"severity": "HIGH", "affected_elements": ["item_0"]})(),
            type("Finding", (), {"severity": "HIGH", "affected_elements": ["item_1"]})(),
            type("Finding", (), {"severity": "HIGH", "affected_elements": ["item_2"]})(),
        ]
        
    monkeypatch.setattr("cipherlens.data_integrity.aggregator.check_spectral_signatures", lambda x, y: [])
    monkeypatch.setattr("cipherlens.data_integrity.aggregator.check_activation_clustering", lambda x, y: [])
    monkeypatch.setattr("cipherlens.data_integrity.aggregator.check_label_consistency", lambda x, y: [])
    monkeypatch.setattr("cipherlens.data_integrity.aggregator.check_duplicates", mock_checks)
    
    findings = run_data_integrity_checks(items, "/dummy")
    
    # We should see the 3 original mocks + 1 aggregation
    assert len(findings) == 4
    agg_finding = findings[-1]
    assert agg_finding.category == "DATA_POISONING"
    assert agg_finding.severity == "CRITICAL"
    assert "contributor_1" in agg_finding.affected_elements
