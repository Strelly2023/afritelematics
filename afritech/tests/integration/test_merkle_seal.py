import pytest
from django.db import connection, transaction

from afritech.models.audit_log import AuditLog
from afritech.services.audit_sealing import seal_epoch, verify_seal


# =====================================================
# ✅ HELPER — CREATE VALID AUDIT LOG
# =====================================================

def create_log(payload, epoch, previous_hash=None):
    """
    Helper to create logs consistently.
    Ensures hash chain integrity if your model uses it.
    """
    return AuditLog.objects.create(
        payload=payload,
        epoch=epoch,
        previous_hash=previous_hash,
    )


# =====================================================
# ✅ TEST 1 — SEAL CREATION
# =====================================================

@pytest.mark.django_db
def test_seal_creation():
    log1 = create_log({"a": 1}, epoch=1)
    log2 = create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal = seal_epoch(epoch=2)

    assert seal is not None
    assert isinstance(seal.merkle_root, str)
    assert len(seal.merkle_root) == 64  # SHA-256 hex length
    assert seal.epoch == 2


# =====================================================
# ✅ TEST 2 — SEAL VERIFICATION (VALID)
# =====================================================

@pytest.mark.django_db
def test_seal_verification():
    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    result = verify_seal(epoch=2)

    assert result is True


# =====================================================
# ✅ TEST 3 — TAMPER DETECTION (CRITICAL)
# =====================================================


@pytest.mark.django_db(transaction=True)
def test_seal_detects_tampering():
    log1 = create_log({"a": 1}, epoch=1)
    log2 = create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    # ✅ FIX: use hex format for SQLite
    db_id = log2.id.hex

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE afritech_auditlog SET entry_hash = %s WHERE id = %s",
            ["fake_hash", db_id],
        )

        # ✅ ensure tampering actually happened
        assert cursor.rowcount == 1, "Tampering update failed"

    transaction.commit()

    result = verify_seal(epoch=2)

    assert result is False, "Tampering was NOT detected"




# =====================================================
# ✅ TEST 4 — SEAL IMMUTABILITY
# =====================================================

@pytest.mark.django_db
def test_seal_immutability():
    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    seal_epoch(epoch=2)

    # modify dataset
    AuditLog.objects.create(payload={"c": 3}, epoch=2)

    with pytest.raises(ValueError) as exc:
        seal_epoch(epoch=2)

    assert "SEAL_ALREADY_EXISTS_WITH_DIFFERENT_ROOT" in str(exc.value)


# =====================================================
# ✅ TEST 5 — EMPTY DATA FAILURE
# =====================================================

@pytest.mark.django_db
def test_seal_fails_without_logs():
    with pytest.raises(ValueError) as exc:
        seal_epoch(epoch=1)

    assert "NO_LOGS_TO_SEAL" in str(exc.value)


# =====================================================
# ✅ TEST 6 — VERIFY FAILS WITH NO SEAL
# =====================================================

@pytest.mark.django_db
def test_verify_without_seal():
    create_log({"a": 1}, epoch=1)

    result = verify_seal(epoch=1)

    assert result is False

import pytest

from afritech.services.audit_sealing import seal_epoch, verify_seal


# =====================================================
# ✅ TEST — SIGNATURE VERIFICATION (VALID CASE)
# =====================================================

@pytest.mark.django_db
def test_seal_signature_verification():
    """
    Ensures that a seal with a valid signature
    verifies successfully.

    This test validates:
    - Merkle root correctness
    - Signature correctness
    - End-to-end integrity flow
    """

    # ✅ Create minimal valid chain
    from afritech.tests.integration.test_merkle_seal import create_log

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    # ✅ Seal (this now also signs the root)
    seal_epoch(epoch=2)

    # ✅ Verify must pass (root + signature)
    result = verify_seal(epoch=2)

    assert result is True, "Valid signature verification failed"
