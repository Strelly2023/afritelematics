from __future__ import annotations

import pytest

from afritech.sdk.partner_verification import PartnerVerificationClient


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def test_partner_sdk_prepares_and_verifies_locally() -> None:
    client = PartnerVerificationClient()
    payload = client.prepare_verify_request(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash=HASH_A,
        replay_hash=HASH_B,
        receipt_hash=HASH_C,
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-sdk-001",
    )

    response = client.verify_locally(payload)

    assert response["verification_status"] == "VERIFIED"
    assert response["publication_target"] == "public-ledger-test-anchor"
    assert response["evidence_pointer"].startswith("anchor:")


def test_partner_sdk_decode_response_requires_fields() -> None:
    client = PartnerVerificationClient()

    with pytest.raises(ValueError, match="missing fields"):
        client.decode_response({"anchor_id": "anchor-1"})
