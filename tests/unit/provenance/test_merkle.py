"""Unit tests for the Merkle tree implementation."""

import pytest

from cipherlens.provenance.merkle import MerkleTree, hash_node
from cipherlens.utils.hashing import sha256_digest


def test_hash_node():
    """Verify hash_node concatenates and hashes correctly."""
    left = sha256_digest(b"a")
    right = sha256_digest(b"b")
    
    # Normal case
    expected_normal = sha256_digest((left + right).encode("utf-8"))
    assert hash_node(left, right) == expected_normal
    
    # Missing right sibling case
    expected_odd = sha256_digest(left.encode("utf-8"))
    assert hash_node(left, "") == expected_odd


def test_merkle_tree_empty():
    """Verify empty tree behavior."""
    tree = MerkleTree([])
    assert tree.root is None
    assert tree.levels == []


def test_merkle_tree_single_leaf():
    """Verify tree with one leaf."""
    leaf = sha256_digest(b"only_leaf")
    tree = MerkleTree([leaf])
    assert tree.root == leaf
    assert len(tree.levels) == 1


def test_merkle_tree_build_and_proof():
    """Verify tree building and proof verification for >= 5 entries."""
    leaves = [sha256_digest(f"leaf_{i}".encode("utf-8")) for i in range(6)]
    tree = MerkleTree(leaves)
    
    assert tree.root is not None
    assert len(tree.levels) > 1
    
    # Check a proof for leaf 2
    proof = tree.get_proof(2)
    assert MerkleTree.verify_proof(leaves[2], proof, tree.root) is True
    
    # Proof should fail for a wrong leaf
    wrong_leaf = sha256_digest(b"wrong")
    assert MerkleTree.verify_proof(wrong_leaf, proof, tree.root) is False


def test_tamper_localization():
    """Verify that tampering with an exact index is localized correctly.
    
    Per PLAN.md Phase 1 DoD: build chain of >= 5, tamper index 2,
    assert it correctly reports index 2.
    """
    original_leaves = [sha256_digest(f"entry_{i}".encode("utf-8")) for i in range(5)]
    tree = MerkleTree(original_leaves)
    original_root = tree.root
    
    # Now simulate a tampered tree where the leaf at index 2 was altered
    tampered_leaves = list(original_leaves)
    tampered_leaves[2] = sha256_digest(b"tampered_payload")
    
    tampered_tree = MerkleTree(tampered_leaves)
    
    # Root must change
    assert tampered_tree.root != original_root
    
    # Localize the tampering
    tampered_indices = tampered_tree.localize_tampering(original_leaves)
    assert tampered_indices == [2]
