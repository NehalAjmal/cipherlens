"""Shared low-level hash helpers used by provenance and dedup modules.

All hash computations in CipherLens route through these functions to ensure
consistency. See AI_RULES.md rule 20 for the canonicalization requirement.
"""

import hashlib
from pathlib import Path


def sha256_digest(data: bytes) -> str:
    """Compute SHA-256 digest of raw bytes.

    Args:
        data: Raw bytes to hash.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Compute SHA-256 digest of a file's contents.

    Reads the file in 8 KiB chunks to handle large files without
    loading them entirely into memory.

    Args:
        path: Path to the file.

    Returns:
        64-character lowercase hex string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
