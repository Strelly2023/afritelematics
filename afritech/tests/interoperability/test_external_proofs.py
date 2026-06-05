from __future__ import annotations

import pytest

from afritech.interoperability.external_proofs import (
    ExternalProofError,
    ingest_external_proof_reference,
    verify_external_proof_reference,
)


@pytest.mark.django_db
def test_external_proof_reference_is_evidence_only_until_verified():
    record = ingest_external_proof_reference(
        external_system="Ethereum",
        transaction_hash="0xabc",
        proof_type="payment",
        raw_reference={"block": 123},
    )

    assert record.independently_verified is False

    verified = verify_external_proof_reference(
        record,
        verification_notes="independently checked receipt",
    )
    assert verified.independently_verified is True


@pytest.mark.django_db
def test_external_proof_verification_requires_notes():
    record = ingest_external_proof_reference(
        external_system="Ethereum",
        transaction_hash="0xdef",
        proof_type="payment",
        raw_reference={},
    )
    with pytest.raises(ExternalProofError, match="notes"):
        verify_external_proof_reference(record, verification_notes="")
