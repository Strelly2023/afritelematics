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
