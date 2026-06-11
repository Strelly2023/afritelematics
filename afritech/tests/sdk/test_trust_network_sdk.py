from __future__ import annotations

from afritech.sdk.trust_network import TrustNetworkClient


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def _partner_payload() -> dict[str, str]:
    return {
        "tenant_id": "tenant-core",
        "region_id": "mel-ap-southeast-2",
        "trace_hash": HASH_A,
        "replay_hash": HASH_B,
        "receipt_hash": HASH_C,
        "authority_hash": HASH_D,
        "execution_fingerprint": HASH_E,
        "publication_target": "public-ledger-test-anchor",
        "external_reference": "ledger-ref-sdk-tn-001",
    }


def test_trust_network_sdk_registers_dependency_and_publishes_registry() -> None:
    client = TrustNetworkClient()
    dependent = client.prepare_dependency_request(
        dependent_id="partner-a-core",
        organization="Partner A",
        use_case="claims validation",
    )

    record = client.register_dependency_locally(dependent)
    registry = client.publish_registry_locally(
        partner_payload=_partner_payload(),
        dependents=(dependent,),
    )

    assert record["status"] == "DECLARED_DEPENDENCY"
    assert registry["dependent_system_count"] == 1
    assert registry["standard_profile"] == "MULTI_PARTY_REPLAY_VERIFICATION_V1"


def test_trust_network_sdk_builds_network_verification_with_dependents() -> None:
    client = TrustNetworkClient()
    network = client.verify_network_locally(
        partner_payload=_partner_payload(),
        dependents=(
            {
                "dependent_id": "partner-a-core",
                "organization": "Partner A",
                "use_case": "claims validation",
            },
        ),
        witnesses=(
            {
                "verifier_id": "v1",
                "organization": "partner-a",
                "decision": "VERIFIED",
                "evidence_hash": "0" * 64,
            },
            {
                "verifier_id": "v2",
                "organization": "partner-b",
                "decision": "VERIFIED",
                "evidence_hash": "1" * 64,
            },
        ),
        quorum=2,
    )

    assert network["aggregate_status"] == "QUORUM_VERIFIED"
    assert network["dependent_system_count"] == 1
