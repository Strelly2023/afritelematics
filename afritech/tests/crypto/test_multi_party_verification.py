from __future__ import annotations

import pytest

from afritech.crypto.multi_party_verification import (
    VerificationWitness,
    build_multi_party_verification_record,
)
from afritech.partner_verification import build_partner_verification_packet


def _packet():
    return build_partner_verification_packet(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash="a" * 64,
        replay_hash="b" * 64,
        receipt_hash="c" * 64,
        authority_hash="d" * 64,
        execution_fingerprint="e" * 64,
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-mpv-001",
    )


def test_multi_party_verification_reaches_quorum() -> None:
    record = build_multi_party_verification_record(
        _packet(),
        (
            VerificationWitness("v1", "partner-a", "VERIFIED", "0" * 64),
            VerificationWitness("v2", "partner-b", "VERIFIED", "1" * 64),
            VerificationWitness("v3", "partner-c", "REJECTED", "2" * 64),
        ),
        quorum=2,
    )

    assert record.aggregate_status == "QUORUM_VERIFIED"
    assert record.verified_count == 2
    assert record.standard_profile == "MULTI_PARTY_REPLAY_VERIFICATION_V1"
    assert len(record.witness_manifest_hash) == 64


def test_multi_party_verification_requires_unique_witnesses() -> None:
    with pytest.raises(ValueError, match="unique"):
        build_multi_party_verification_record(
            _packet(),
            (
                VerificationWitness("v1", "partner-a", "VERIFIED", "0" * 64),
                VerificationWitness("v1", "partner-b", "VERIFIED", "1" * 64),
            ),
            quorum=2,
        )
