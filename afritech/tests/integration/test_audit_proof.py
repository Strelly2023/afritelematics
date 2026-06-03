import pytest

from afritech.services.audit_sealing import seal_epoch
from afritech.services.audit_proof import export_audit_proof
from afritech.services.audit_proof_verifier import verify_audit_proof
from afritech.tests.integration.test_merkle_seal import create_log


# =====================================================
# ✅ TEST 1 — EXPORT + VERIFY (VALID CASE)
# =====================================================

@pytest.mark.django_db
def test_audit_proof_export_and_verify():
    """
    Ensures:
    - proof export is correct
    - external verification succeeds
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # ✅ structural validation
    assert isinstance(proof, dict)
    assert "merkle_root" in proof
    assert "signature" in proof
    assert "logs" in proof
    assert isinstance(proof["logs"], list)
    assert len(proof["logs"]) == 2

    # ✅ verification must succeed
    assert verify_audit_proof(proof) is True


# =====================================================
# ✅ TEST 2 — DETECT PAYLOAD TAMPERING
# =====================================================

@pytest.mark.django_db
def test_audit_proof_detects_payload_tampering():
    """
    Ensures payload modification breaks proof validity.
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 tamper payload
    proof["logs"][0]["payload"]["a"] = 999

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 3 — DETECT HASH TAMPERING
# =====================================================

@pytest.mark.django_db
def test_audit_proof_detects_hash_tampering():
    """
    Ensures entry_hash tampering is detected.
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 tamper entry hash
    proof["logs"][0]["entry_hash"] = "fake_hash"

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 4 — DETECT MERKLE ROOT TAMPERING
# =====================================================

@pytest.mark.django_db
def test_audit_proof_detects_root_tampering():
    """
    Ensures Merkle root modification invalidates proof.
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 tamper root
    proof["merkle_root"] = "fake_root"

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 5 — DETECT SIGNATURE TAMPERING
# =====================================================

@pytest.mark.django_db
def test_audit_proof_detects_signature_tampering():
    """
    Ensures signature modification invalidates proof.
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 tamper signature
    proof["signature"] = "fake_signature"

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 6 — INVALID STRUCTURE
# =====================================================

@pytest.mark.django_db
def test_audit_proof_invalid_structure():
    """
    Ensures malformed proofs are rejected.
    """

    proof = {
        "merkle_root": None,
        "signature": None,
        "logs": []
    }

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 7 — DETECT LOG ORDER TAMPERING
# =====================================================

@pytest.mark.django_db
def test_audit_proof_detects_log_reordering():
    """
    Ensures reordering logs breaks chain validation.
    """

    log1 = create_log({"a": 1}, epoch=1)
    log2 = create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 reverse logs (breaks chain)
    proof["logs"] = list(reversed(proof["logs"]))

    assert verify_audit_proof(proof) is False


# =====================================================
# ✅ TEST 8 — DETECT MISSING FIELD
# =====================================================

@pytest.mark.django_db
def test_audit_proof_missing_field():
    """
    Ensures missing required fields invalidate proof.
    """

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    proof = export_audit_proof(epoch=2)

    # 🔥 remove field
    del proof["logs"][0]["entry_hash"]

    assert verify_audit_proof(proof) is False