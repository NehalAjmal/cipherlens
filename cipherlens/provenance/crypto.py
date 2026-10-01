"""Cryptography and provenance record generation for CipherLens.

Implements Ed25519 signing/verification and canonical JSON serialization
per BACKEND_SCHEMA.md §4.

Note on security invariants:
Digest canonicalization is always `json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=False)`
"""

import json
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from cipherlens.utils.hashing import sha256_digest


def canonicalize(obj: dict[str, Any]) -> str:
    """Serialize a dictionary to a canonical JSON string.

    Uses strict settings to ensure byte-for-byte identical output for
    identical data, which is required for stable hashing and signatures.
    Per AI_RULES.md, do NOT change these kwargs.

    Args:
        obj: The dictionary to serialize.

    Returns:
        The canonical JSON string.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def generate_keypair() -> tuple[str, str]:
    """Generate a new Ed25519 keypair.

    Returns:
        A tuple of (private_key_pem, public_key_pem) as strings.
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_bytes.decode("utf-8"), public_bytes.decode("utf-8")


def sign_payload(payload: dict[str, Any], private_key_pem: str) -> str:
    """Sign a canonicalized dictionary using an Ed25519 private key.

    Args:
        payload: The dictionary to sign.
        private_key_pem: The PEM-encoded private key.

    Returns:
        The signature as a hex string.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )
    if not isinstance(private_key, ed25519.Ed25519PrivateKey):
        raise TypeError("Private key must be Ed25519")

    canonical_json = canonicalize(payload)
    signature = private_key.sign(canonical_json.encode("utf-8"))
    return signature.hex()


def verify_signature(payload: dict[str, Any], signature_hex: str, public_key_pem: str) -> bool:
    """Verify a signature against a payload using an Ed25519 public key.

    Args:
        payload: The dictionary that was signed.
        signature_hex: The hex-encoded signature.
        public_key_pem: The PEM-encoded public key.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, ed25519.Ed25519PublicKey):
            raise TypeError("Public key must be Ed25519")

        canonical_json = canonicalize(payload)
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, canonical_json.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def generate_provenance_record(
    actor_id: str,
    operation: str,
    inputs_hash: str,
    outputs_hash: str,
    config_hash: str,
    private_key_pem: str,
    public_key_pem: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Generate a signed provenance record per BACKEND_SCHEMA.md §4.

    Args:
        actor_id: Identifier for the entity performing the operation.
        operation: Name of the operation (e.g., 'DATA_INTEGRITY_SCAN').
        inputs_hash: Hash of the input data (e.g., dataset/model).
        outputs_hash: Hash of the generated findings/report.
        config_hash: Hash of the configuration used.
        private_key_pem: The actor's Ed25519 private key.
        public_key_pem: The actor's Ed25519 public key (included in record for verification).
        timestamp: Optional ISO 8601 UTC timestamp. If None, current time is used.

    Returns:
        A dictionary containing the signed record.
    """
    if timestamp is None:
        # e.g., '2024-03-20T10:15:30Z'
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the base payload (everything except the signature itself)
    payload = {
        "timestamp": timestamp,
        "actor_id": actor_id,
        "operation": operation,
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "config_hash": config_hash,
        "public_key": public_key_pem,
    }

    # Sign the canonicalized base payload
    signature = sign_payload(payload, private_key_pem)

    # Return the complete record
    record = payload.copy()
    record["signature"] = signature
    return record


def verify_provenance_record(record: dict[str, Any]) -> bool:
    """Verify a signed provenance record.

    Validates that the signature matches the canonicalized fields
    (excluding the signature field itself).

    Args:
        record: The complete provenance record dictionary.

    Returns:
        True if valid, False otherwise.
    """
    # Extract signature and base payload
    signature_hex = record.get("signature")
    if not signature_hex:
        return False

    # The payload to verify is the record without the 'signature' field
    payload = {k: v for k, v in record.items() if k != "signature"}
    public_key_pem = record.get("public_key")
    if not public_key_pem:
         return False

    return verify_signature(payload, signature_hex, public_key_pem)
