import pytest

from afritech.audit.merkle import MerkleTree
from afritech.models.audit_log import AuditLog


# =====================================================
# ✅ TEST 1 — MERKLE ROOT CONSISTENCY
# =====================================================

@pytest.mark.django_db
def test_merkle_root_consistency():
    """
    The same dataset must always produce the same Merkle root.
    """

    AuditLog.objects.create(payload={"a": 1}, epoch=1)
    AuditLog.objects.create(payload={"b": 2}, epoch=2)
    AuditLog.objects.create(payload={"c": 3}, epoch=3)

    root1 = AuditLog.compute_merkle_root()
    root2 = AuditLog.compute_merkle_root()

    assert root1 == root2
    assert isinstance(root1, str)
    assert len(root1) == 64  # SHA-256


# =====================================================
# ✅ TEST 2 — MERKLE TREE BUILD (MANUAL HASHES)
# =====================================================

def test_merkle_tree_structure():
    """
    Ensures Merkle tree builds correct levels.
    """

    leaves = ["a", "b", "c", "d"]

    tree = MerkleTree(leaves)

    # ✅ Root must exist
    root = tree.get_root()
    assert root is not None

    # ✅ Tree levels should be > 1
    assert len(tree.levels) >= 2

    # ✅ Last level must have 1 element (root)
    assert len(tree.levels[-1]) == 1


# =====================================================
# ✅ TEST 3 — MERKLE PROOF VERIFICATION
# =====================================================

def test_merkle_proof_verification():
    """
    Validates inclusion proof for a leaf node.
    """

    leaves = ["h1", "h2", "h3", "h4"]

    tree = MerkleTree(leaves)

    index = 2  # h3
    leaf = leaves[index]

    proof = tree.get_proof(index)
    root = tree.get_root()

    assert MerkleTree.verify_proof(leaf, proof, root) is True


# =====================================================
# ✅ TEST 4 — MERKLE PROOF FAILURE (TAMPER)
# =====================================================

def test_merkle_proof_failure():
    """
    Proof must fail if leaf is tampered.
    """

    leaves = ["h1", "h2", "h3", "h4"]

    tree = MerkleTree(leaves)

    proof = tree.get_proof(2)
    root = tree.get_root()

    # 🔥 tampered leaf
    fake_leaf = "fake_hash"

    assert MerkleTree.verify_proof(fake_leaf, proof, root) is False


# =====================================================
# ✅ TEST 5 — MERKLE ROOT FROM AUDIT LOG
# =====================================================

@pytest.mark.django_db
def test_merkle_root_from_audit_log():
    """
    Ensures audit log integrates correctly with Merkle tree.
    """

    AuditLog.objects.create(payload={"x": 10}, epoch=1)
    AuditLog.objects.create(payload={"y": 20}, epoch=2)

    root = AuditLog.compute_merkle_root()

    assert root is not None
    assert isinstance(root, str)
    assert len(root) == 64


# =====================================================
# ✅ TEST 6 — MERKLE ROOT CHANGES ON DATA CHANGE
# =====================================================

@pytest.mark.django_db
def test_merkle_root_changes_on_data_change():
    """
    Any change in data must produce a different root.
    """

    AuditLog.objects.create(payload={"a": 1}, epoch=1)
    root1 = AuditLog.compute_merkle_root()

    AuditLog.objects.create(payload={"b": 2}, epoch=2)
    root2 = AuditLog.compute_merkle_root()

    assert root1 != root2


# =====================================================
# ✅ TEST 7 — ODD NUMBER OF LEAVES HANDLING
# =====================================================

def test_merkle_odd_leaves():
    """
    Tests correct handling of odd number of leaves.
    """

    leaves = ["h1", "h2", "h3"]  # odd count

    tree = MerkleTree(leaves)

    root = tree.get_root()

    assert root is not None
    assert isinstance(root, str)

    # Proof should still work
    proof = tree.get_proof(2)
    assert MerkleTree.verify_proof("h3", proof, root)


# =====================================================
# ✅ TEST 8 — EMPTY TREE SHOULD FAIL
# =====================================================

def test_empty_merkle_tree():
    """
    Merkle tree should reject empty input.
    """

    with pytest.raises(ValueError):
        MerkleTree([])