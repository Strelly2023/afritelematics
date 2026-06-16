"""Level 14 multi-node federated trust-network model."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from afritech.features import registry_payload
from afritech.security.key_manager import DeterministicLocalSigningProvider
from afritech.security.signing import verify_signature


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FederatedTrustNode:
    node_id: str
    organization: str
    jurisdiction: str
    roles: tuple[str, ...]
    public_key: str
    status: str = "TRUSTED"

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FederatedTrustWitness:
    node_id: str
    decision: str
    registry_hash: str
    signature: str
    public_key: str

    def canonical_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FederatedTrustCertificate:
    certificate_id: str
    classification: str
    level: str
    quorum: int
    node_count: int
    verified_count: int
    aggregate_status: str
    registry_hash: str
    network_hash: str
    nodes: tuple[FederatedTrustNode, ...]
    witnesses: tuple[FederatedTrustWitness, ...]
    authority_boundary: str = "federated_network_verifies_registry_without_creating_runtime_authority"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.federated_trust_certificate.v1",
            "certificate_id": self.certificate_id,
            "classification": self.classification,
            "level": self.level,
            "quorum": self.quorum,
            "node_count": self.node_count,
            "verified_count": self.verified_count,
            "aggregate_status": self.aggregate_status,
            "registry_hash": self.registry_hash,
            "network_hash": self.network_hash,
            "nodes": [node.canonical_dict() for node in self.nodes],
            "witnesses": [witness.canonical_dict() for witness in self.witnesses],
            "authority_boundary": self.authority_boundary,
        }


def default_federated_nodes() -> tuple[FederatedTrustNode, ...]:
    return tuple(
        _node(
            node_id=node_id,
            organization=organization,
            jurisdiction=jurisdiction,
            roles=roles,
        )
        for node_id, organization, jurisdiction, roles in (
            ("afritech-core-node", "AfriTech Core", "protocol", ("CORE", "REGISTRY_SIGNER")),
            ("partner-verifier-node", "External Partner Verifier", "commercial", ("PARTNER", "VERIFIER")),
            ("government-observer-node", "Government Observer", "public-sector", ("GOVERNMENT", "OBSERVER")),
        )
    )


def build_federated_trust_certificate(
    registry: dict[str, Any] | None = None,
    *,
    quorum: int = 2,
) -> FederatedTrustCertificate:
    payload = registry or registry_payload()
    registry_hash = str(payload["registry_hash"])
    nodes = default_federated_nodes()
    witnesses = tuple(_witness(node, registry_hash) for node in nodes)
    verified_count = sum(1 for witness in witnesses if _witness_valid(witness))
    aggregate_status = "FEDERATED_QUORUM_VERIFIED" if verified_count >= quorum else "FEDERATED_QUORUM_FAILED"
    network_hash = _hash(
        {
            "registry_hash": registry_hash,
            "quorum": quorum,
            "nodes": [node.canonical_dict() for node in nodes],
            "witnesses": [witness.canonical_dict() for witness in witnesses],
        }
    )
    return FederatedTrustCertificate(
        certificate_id=f"ftc-{network_hash[:12]}",
        classification="LEVEL_14_FEDERATED_TRUST_NETWORK",
        level="LEVEL_14",
        quorum=quorum,
        node_count=len(nodes),
        verified_count=verified_count,
        aggregate_status=aggregate_status,
        registry_hash=registry_hash,
        network_hash=network_hash,
        nodes=nodes,
        witnesses=witnesses,
    )


def verify_federated_trust_certificate(
    certificate: FederatedTrustCertificate | dict[str, Any],
) -> dict[str, object]:
    payload = (
        certificate.canonical_dict()
        if isinstance(certificate, FederatedTrustCertificate)
        else certificate
    )
    witnesses = payload.get("witnesses", [])
    quorum = int(payload.get("quorum", 0))
    verified_count = sum(1 for witness in witnesses if _witness_payload_valid(witness))
    verified = (
        payload.get("classification") == "LEVEL_14_FEDERATED_TRUST_NETWORK"
        and verified_count >= quorum
        and payload.get("aggregate_status") == "FEDERATED_QUORUM_VERIFIED"
    )
    return {
        "verified": verified,
        "classification": payload.get("classification"),
        "level": payload.get("level"),
        "quorum": quorum,
        "node_count": payload.get("node_count"),
        "verified_count": verified_count,
        "registry_hash": payload.get("registry_hash"),
        "network_hash": payload.get("network_hash"),
        "aggregate_status": payload.get("aggregate_status"),
        "public_sector_ready": any(
            "GOVERNMENT" in node.get("roles", [])
            for node in payload.get("nodes", [])
        ),
        "partner_ready": any(
            "PARTNER" in node.get("roles", [])
            for node in payload.get("nodes", [])
        ),
        "authority_boundary": payload.get("authority_boundary"),
    }


def _node(
    *,
    node_id: str,
    organization: str,
    jurisdiction: str,
    roles: tuple[str, ...],
) -> FederatedTrustNode:
    provider = DeterministicLocalSigningProvider(signer_id=node_id)
    return FederatedTrustNode(
        node_id=node_id,
        organization=organization,
        jurisdiction=jurisdiction,
        roles=roles,
        public_key=provider.public_key().hex(),
    )


def _witness(node: FederatedTrustNode, registry_hash: str) -> FederatedTrustWitness:
    provider = DeterministicLocalSigningProvider(signer_id=node.node_id)
    return FederatedTrustWitness(
        node_id=node.node_id,
        decision="VERIFIED",
        registry_hash=registry_hash,
        signature=provider.sign(registry_hash.encode("utf-8")).hex(),
        public_key=node.public_key,
    )


def _witness_valid(witness: FederatedTrustWitness) -> bool:
    return _witness_payload_valid(witness.canonical_dict())


def _witness_payload_valid(payload: dict[str, Any]) -> bool:
    return (
        payload.get("decision") == "VERIFIED"
        and isinstance(payload.get("registry_hash"), str)
        and isinstance(payload.get("signature"), str)
        and isinstance(payload.get("public_key"), str)
        and verify_signature(
            str(payload["public_key"]),
            str(payload["signature"]),
            str(payload["registry_hash"]),
        )
    )


__all__ = [
    "FederatedTrustCertificate",
    "FederatedTrustNode",
    "FederatedTrustWitness",
    "build_federated_trust_certificate",
    "default_federated_nodes",
    "verify_federated_trust_certificate",
]
