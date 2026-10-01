"""Unit tests for the provenance cryptography module.

Ensures that strict JSON canonicalization and Ed25519 signatures
prevent any single-field tampering.
"""

import copy

import pytest

from cipherlens.provenance.crypto import (
    canonicalize,
    generate_keypair,
    generate_provenance_record,
    sign_payload,
    verify_provenance_record,
    verify_signature,
)


def test_canonicalize_stable():
    """Verify that canonicalization produces stable output regardless of input dict order."""
    obj1 = {"b": 2, "a": 1, "c": {"z": 9, "y": 8}}
    obj2 = {"c": {"y": 8, "z": 9}, "a": 1, "b": 2}
    
    # Must use no-space separators and sort keys
    expected = '{"a":1,"b":2,"c":{"y":8,"z":9}}'
    assert canonicalize(obj1) == expected
    assert canonicalize(obj2) == expected


def test_sign_verify_roundtrip():
    """Verify that a signed payload can be successfully verified."""
    private_key, public_key = generate_keypair()
    payload = {"foo": "bar", "baz": 123}
    
    signature = sign_payload(payload, private_key)
    assert verify_signature(payload, signature, public_key) is True


def test_verify_fails_on_tampered_payload():
    """Verify that changing the payload breaks the signature."""
    private_key, public_key = generate_keypair()
    payload = {"foo": "bar"}
    signature = sign_payload(payload, private_key)
    
    tampered_payload = {"foo": "baz"}
    assert verify_signature(tampered_payload, signature, public_key) is False


def test_generate_and_verify_provenance_record():
    """Verify that a full provenance record validates."""
    private_key, public_key = generate_keypair()
    
    record = generate_provenance_record(
        actor_id="test_runner",
        operation="SCAN",
        inputs_hash="abc",
        outputs_hash="def",
        config_hash="123",
        private_key_pem=private_key,
        public_key_pem=public_key,
    )
    
    assert verify_provenance_record(record) is True


def test_provenance_record_tampering_fails_every_field():
    """Verify that altering ANY field independently breaks verification.
    
    This fulfills the explicit requirement in PLAN.md Phase 1 DoD.
    """
    private_key, public_key = generate_keypair()
    
    base_record = generate_provenance_record(
        actor_id="test_runner",
        operation="SCAN",
        inputs_hash="abc",
        outputs_hash="def",
        config_hash="123",
        private_key_pem=private_key,
        public_key_pem=public_key,
    )
    assert verify_provenance_record(base_record) is True
    
    # 1. Tamper timestamp
    record = copy.deepcopy(base_record)
    record["timestamp"] = "1999-01-01T00:00:00Z"
    assert verify_provenance_record(record) is False
    
    # 2. Tamper actor_id
    record = copy.deepcopy(base_record)
    record["actor_id"] = "evil_runner"
    assert verify_provenance_record(record) is False
    
    # 3. Tamper operation
    record = copy.deepcopy(base_record)
    record["operation"] = "BYPASS"
    assert verify_provenance_record(record) is False
    
    # 4. Tamper inputs_hash
    record = copy.deepcopy(base_record)
    record["inputs_hash"] = "tampered"
    assert verify_provenance_record(record) is False
    
    # 5. Tamper outputs_hash
    record = copy.deepcopy(base_record)
    record["outputs_hash"] = "tampered"
    assert verify_provenance_record(record) is False
    
    # 6. Tamper config_hash
    record = copy.deepcopy(base_record)
    record["config_hash"] = "tampered"
    assert verify_provenance_record(record) is False
    
    # 7. Tamper public_key (someone trying to swap keys but keeping the original signature)
    _, evil_pub = generate_keypair()
    record = copy.deepcopy(base_record)
    record["public_key"] = evil_pub
    assert verify_provenance_record(record) is False
    
    # 8. Tamper signature directly (e.g. flip one character)
    record = copy.deepcopy(base_record)
    sig = record["signature"]
    # Change last char: if it's 'a', make it 'b', else make it 'a'
    flipped_char = 'b' if sig[-1] == 'a' else 'a'
    record["signature"] = sig[:-1] + flipped_char
    assert verify_provenance_record(record) is False
    
    # 9. Add a completely new unexpected field
    record = copy.deepcopy(base_record)
    record["sneaky_extra_field"] = "hidden_data"
    assert verify_provenance_record(record) is False
