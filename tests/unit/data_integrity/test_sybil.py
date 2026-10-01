import pytest
from datetime import datetime, timezone, timedelta
from cipherlens.ingestion.unified_schema import DatasetItem, AcquisitionMeta, Annotation
from cipherlens.utils.finding import Finding
from cipherlens.data_integrity.sybil import check_sybil_heuristics

def create_dummy_item(item_id, contributor_id, ts_iso):
    return DatasetItem(
        item_id=item_id,
        image_path=f"{item_id}.jpg",
        image_sha256="fake_hash",
        width=100,
        height=100,
        annotations=[],
        contributor_id=contributor_id,
        batch_id="b1",
        source_format="YOLO",
        acquisition_meta=AcquisitionMeta(timestamp=ts_iso)
    )

def test_sybil_cross_contributor_overlap():
    items = [
        create_dummy_item("img1", "alice", "2023-01-01T12:00:00Z"),
        create_dummy_item("img2", "bob", "2023-01-01T12:00:01Z")
    ]
    # Simulate a deduplication finding where alice and bob submitted near-duplicates
    findings = [
        Finding(
            category="NEAR_DUPLICATE",
            severity="LOW",
            confidence=0.99,
            reason="Near-duplicate images detected",
            evidence={},
            affected_elements=["img1", "img2"]
        )
    ]
    
    sybil_findings = check_sybil_heuristics(items, findings)
    assert len(sybil_findings) == 1
    assert sybil_findings[0].category == "SYBIL_RISK"
    assert "Cross-contributor duplicate overlap" in sybil_findings[0].reason
    assert set(sybil_findings[0].affected_elements) == {"alice", "bob"}


def test_sybil_velocity_anomaly():
    items = []
    base_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # Charlie submits 10 items in 0.5 seconds (anomalous)
    for i in range(10):
        ts = base_time + timedelta(milliseconds=i * 50)
        items.append(create_dummy_item(f"c_img{i}", "charlie", ts.isoformat()))
        
    # Dave submits 10 items over 10 minutes (normal)
    for i in range(10):
        ts = base_time + timedelta(minutes=i)
        items.append(create_dummy_item(f"d_img{i}", "dave", ts.isoformat()))

    sybil_findings = check_sybil_heuristics(items, [])
    
    # We expect 1 finding for charlie's velocity
    assert len(sybil_findings) == 1
    assert sybil_findings[0].category == "SYBIL_RISK"
    assert sybil_findings[0].affected_elements == ["charlie"]
    assert "Velocity anomaly" in sybil_findings[0].reason
