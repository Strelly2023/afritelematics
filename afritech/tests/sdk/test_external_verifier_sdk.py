from __future__ import annotations

from afritech.architecture.integrity_proof import build_architecture_integrity_proof, build_partner_demo_payload
from afritech.sdk.external_verifier import ExternalVerifierClient


def _proof_payload() -> dict[str, object]:
    proof = build_architecture_integrity_proof().canonical_dict()
    return {
        "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
        "authority_boundary": proof["authority_boundary"],
        "proof": proof,
    }


def test_external_verifier_sdk_decodes_architecture_proof() -> None:
    client = ExternalVerifierClient()

    payload = client.decode_architecture_proof_response(_proof_payload())

    assert payload["proof"]["verification_packet"]["verification_status"] == "VERIFIED"


def test_external_verifier_sdk_verifies_chain_receipt_locally() -> None:
    client = ExternalVerifierClient()

    result = client.verify_architecture_proof_locally(_proof_payload())

    assert result["verification_status"] == "VERIFIED"
    assert result["chain_receipt_matches"] is True


def test_external_verifier_sdk_decodes_partner_demo_narrative() -> None:
    client = ExternalVerifierClient()

    payload = client.decode_partner_demo_narrative(build_partner_demo_payload())

    assert payload["demo_readiness"] == "PARTNER_READY"


def test_external_verifier_sdk_decodes_public_trust_dashboard() -> None:
    client = ExternalVerifierClient()
    proof = build_architecture_integrity_proof().canonical_dict()

    payload = client.decode_public_trust_dashboard(
        {
            "classification": "PUBLIC_TRUST_DASHBOARD",
            "integrity": {"proof_id": proof["proof_id"]},
            "chain": {"deterministic_receipt": proof["public_chain_receipt"]},
            "surfaces": [{"label": "Architecture proof", "path": "/public/architecture/proof"}],
        }
    )

    assert payload["classification"] == "PUBLIC_TRUST_DASHBOARD"
