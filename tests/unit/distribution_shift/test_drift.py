"""Unit tests for MMD and KS drift detection."""

import numpy as np

from cipherlens.distribution_shift.ks_test import check_ks_drift
from cipherlens.distribution_shift.mmd import check_mmd


def test_mmd_no_drift():
    """Verify MMD^2 is near zero when there is no distribution shift."""
    np.random.seed(42)
    ref = np.random.randn(50, 10)
    test = ref.copy() # exact same data
    
    findings = check_mmd(ref, test)
    # Shouldn't flag any findings
    assert len(findings) == 0


def test_mmd_with_drift():
    """Verify MMD flags when shift is large."""
    np.random.seed(42)
    ref = np.random.randn(50, 10)
    test = np.random.randn(50, 10) + 5.0 # severe mean shift
    
    findings = check_mmd(ref, test)
    assert len(findings) == 1
    assert findings[0].category == "DISTRIBUTION_SHIFT"


def test_ks_no_drift():
    """Verify KS doesn't flag identical distributions."""
    np.random.seed(42)
    ref = np.random.randn(50, 10)
    test = ref.copy()
    
    findings = check_ks_drift(ref, test)
    assert len(findings) == 0


def test_ks_with_drift():
    """Verify KS flags severe drift."""
    np.random.seed(42)
    ref = np.random.randn(50, 10)
    test = np.random.randn(50, 10) + 5.0
    
    findings = check_ks_drift(ref, test)
    assert len(findings) == 1
    assert findings[0].category == "DISTRIBUTION_SHIFT"
