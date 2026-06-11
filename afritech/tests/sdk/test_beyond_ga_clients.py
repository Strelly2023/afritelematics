from __future__ import annotations

from afritech.sdk.partner_registry import PartnerRegistryClient
from afritech.sdk.public_verifier import PublicVerifierClient


def test_partner_registry_client_builds_registration_payload() -> None:
    client = PartnerRegistryClient()

    payload = client.prepare_registration_request(
        partner_id="partner-bank-1",
        organization="Evidence Banking Group",
        sector="finance",
        region_id="nbo-af-east-1",
    )

    assert payload["partner_id"] == "partner-bank-1"
    assert payload["integration_stage"] == "discovery"


def test_public_verifier_client_validates_payload_shape() -> None:
    client = PublicVerifierClient()

    payload = client.decode_public_verification(
        {
            "classification": "CONTROLLED_PUBLIC_VERIFICATION",
            "packet": {"anchor_id": "anchor-123"},
            "registry_entry": {"anchor_id": "anchor-123"},
        }
    )

    assert payload["packet"]["anchor_id"] == "anchor-123"


def test_public_verifier_client_validates_architecture_proof_payload() -> None:
    client = PublicVerifierClient()

    payload = client.decode_architecture_proof(
        {
            "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
            "proof": {
                "anchor_commitment": {"anchor_id": "anchor-arch-1"},
                "publication_envelope": {"publication_id": "publish-1"},
                "verification_packet": {"verification_status": "VERIFIED"},
                "registry_entry": {"registry_id": "registry-1"},
            },
        }
    )

    assert payload["proof"]["verification_packet"]["verification_status"] == "VERIFIED"


def test_public_verifier_client_validates_system_integrity_demo_payload() -> None:
    client = PublicVerifierClient()

    payload = client.decode_system_integrity_demo(
        {
            "classification": "PARTNER_LIVE_SYSTEM_INTEGRITY_DEMO",
            "walkthrough": [{"step": 1}],
            "proof": {"proof_id": "arch-proof-1"},
        }
    )

    assert payload["proof"]["proof_id"] == "arch-proof-1"
