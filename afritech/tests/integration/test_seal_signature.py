import pytest

from afritech.models.audit_seal import AuditSeal
from afritech.services.audit_sealing import seal_epoch, verify_seal


@pytest.mark.django_db
def test_signature_detects_tampering():
    """
    Ensures that modifying the signature invalidates the seal.
    """

    from afritech.tests.integration.test_merkle_seal import create_log

    log1 = create_log({"a": 1}, epoch=1)
    create_log({"b": 2}, epoch=2, previous_hash=log1.entry_hash)

    # ✅ Create signed seal
    seal = seal_epoch(epoch=2)

    # 🔥 Tamper signature
    seal.signature = "fake_signature"
    seal.save(update_fields=["signature"])

    # ✅ Must fail
    result = verify_seal(epoch=2)

    assert result is False, "Tampered signature was NOT detected"
