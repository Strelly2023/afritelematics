from __future__ import annotations

from afritech.features import registry_payload
from afritech.security.key_manager import DeterministicLocalSigningProvider
from afritech.security.trust_registry import build_default_trust_registry, signer_authorized
from afritech.trust_federation import (
    build_federated_trust_certificate,
    verify_federated_trust_certificate,
)


def test_signer_governance_authorizes_registry_signer():
    payload = registry_payload()
    signature = payload["signature"]
    registry = build_default_trust_registry(signature["public_key"])

    assert signer_authorized(payload, registry) is True


def test_signer_governance_rejects_revoked_key():
    payload = registry_payload()
    signature = payload["signature"]
    registry = build_default_trust_registry(signature["public_key"])
    revoked = type(registry)(
        signers=registry.signers,
        revoked_keys=(signature["public_key"],),
    )

    assert signer_authorized(payload, revoked) is False


def test_trust_root_provider_exposes_non_derivable_interface():
    provider = DeterministicLocalSigningProvider(signer_id="test-node")

    signature = provider.sign(b"registry-hash")

    assert provider.signer_id == "test-node"
    assert provider.public_key()
    assert signature


def test_level14_federated_trust_certificate_reaches_quorum():
    certificate = build_federated_trust_certificate(registry_payload())
    verification = verify_federated_trust_certificate(certificate)

    assert certificate.classification == "LEVEL_14_FEDERATED_TRUST_NETWORK"
    assert certificate.node_count == 3
    assert certificate.quorum == 2
    assert certificate.aggregate_status == "FEDERATED_QUORUM_VERIFIED"
    assert verification["verified"] is True
    assert verification["partner_ready"] is True
    assert verification["public_sector_ready"] is True


def test_level14_federated_trust_rejects_tampered_witness():
    certificate = build_federated_trust_certificate(registry_payload()).canonical_dict()
    certificate["witnesses"][0]["signature"] = "00"
    verification = verify_federated_trust_certificate(certificate)

    assert verification["verified"] is True
    assert verification["verified_count"] == 2

    certificate["witnesses"][1]["signature"] = "00"
    verification = verify_federated_trust_certificate(certificate)
    assert verification["verified"] is False
    assert verification["verified_count"] == 1
