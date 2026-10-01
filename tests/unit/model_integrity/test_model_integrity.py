"""Unit tests for the Model Integrity module.

Tests true-negative behavior on a clean model and access tier resolution.
"""

from pathlib import Path

import pytest

from cipherlens.ingestion.model_loader import load_model
from cipherlens.model_integrity import analyze
from cipherlens.model_integrity.access_tier import determine_access_tier


@pytest.fixture(scope="module")
def clean_model_handle():
    """Load the clean cached ResNet-18 backbone."""
    model_path = Path("models_cache/backbone/resnet18.pt")
    if not model_path.exists():
        pytest.skip("Reference backbone not downloaded. Run scripts/download_reference_backbone.py.")
    from unittest import mock
    with mock.patch("cipherlens.ingestion.sandbox.run_in_docker_sandbox"):
        return load_model(str(model_path), "resnet18_clean", access_tier_available="WHITE_BOX")


def test_access_tier_resolution(clean_model_handle):
    """Verify tier resolution uses manifest and respects overrides."""
    # PyTorch loader should set it to WHITE_BOX by default
    assert clean_model_handle.manifest.access_tier_available == "WHITE_BOX"
    
    tier = determine_access_tier(clean_model_handle)
    assert tier == "WHITE_BOX"
    
    tier_override = determine_access_tier(clean_model_handle, override="BLACK_BOX")
    assert tier_override == "BLACK_BOX"


def test_white_box_clean_model(clean_model_handle):
    """Verify a clean model produces no high-confidence/CRITICAL backdoor findings in WHITE_BOX mode."""
    findings = analyze(clean_model_handle, override_tier="WHITE_BOX")
    
    # We should have NO CRITICAL findings, and ideally no HIGH findings either
    # for a standard clean backbone.
    for f in findings:
        assert f.severity != "CRITICAL"
        assert f.severity != "HIGH", f"Unexpected HIGH severity finding: {f.reason}"
        assert f.access_tier == "WHITE_BOX"


def test_black_box_clean_model(clean_model_handle):
    """Verify black-box mode handles Neural Cleanse gracefully and runs STRIP."""
    findings = analyze(clean_model_handle, override_tier="BLACK_BOX")
    
    # Check that Neural Cleanse reported it was unavailable
    nc_unavailable = any(
        "Neural Cleanse unavailable" in f.reason for f in findings
    )
    assert nc_unavailable, "Neural Cleanse should report unavailable in BLACK_BOX mode"
    
    # Check that no CRITICAL/HIGH false positives occurred
    high_critical_findings = [f for f in findings if f.severity in ("HIGH", "CRITICAL")]
    assert len(high_critical_findings) == 0, f"Unexpected high/critical findings: {high_critical_findings}"
    
    for f in findings:
        assert f.access_tier == "BLACK_BOX"
