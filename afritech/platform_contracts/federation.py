"""Version-vector negotiation for NovaFederation peers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from afritech.platform_contracts.registry import (
    ContractRegistryError,
    current_version_vector,
    negotiate_version,
)


SUPPORTED_SIGNATURE_ALGORITHMS = (
    "ed25519",
    "ecdsa-p256-sha256",
    "rsa-pss-sha256",
)


@dataclass(frozen=True)
class FederationManifest:
    node_id: str
    versions: Mapping[str, str]
    signature_algorithms: tuple[str, ...]
    capabilities: tuple[str, ...]
    authority_boundary: str = "verification_only"

    def canonical(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "versions": dict(self.versions),
            "signature_algorithms": list(self.signature_algorithms),
            "capabilities": list(self.capabilities),
            "authority_boundary": self.authority_boundary,
        }


def local_federation_manifest(node_id: str = "novatech-local") -> FederationManifest:
    vector = current_version_vector()
    return FederationManifest(
        node_id=node_id,
        versions={
            "contract": vector.contract,
            "replay": vector.replay,
            "evidence": vector.evidence,
            "signature": vector.signature,
        },
        signature_algorithms=SUPPORTED_SIGNATURE_ALGORITHMS,
        capabilities=("trust_exchange", "remote_verification", "remote_replay"),
    )


def negotiate_federation_manifest(remote: FederationManifest) -> dict[str, Any]:
    if remote.authority_boundary != "verification_only":
        raise ContractRegistryError("federation_peer_requests_execution_authority")
    negotiations = [
        negotiate_version(dimension, version)
        for dimension, version in remote.versions.items()
        if dimension in {"contract", "replay", "evidence", "signature"}
    ]
    algorithms = [
        algorithm
        for algorithm in SUPPORTED_SIGNATURE_ALGORITHMS
        if algorithm in remote.signature_algorithms
    ]
    compatible = (
        len(negotiations) == 4
        and all(item.status == "COMPATIBLE" for item in negotiations)
        and bool(algorithms)
    )
    return {
        "status": "COMPATIBLE" if compatible else "UNSUPPORTED",
        "peer_node_id": remote.node_id,
        "negotiations": [item.canonical() for item in negotiations],
        "selected_signature_algorithm": algorithms[0] if algorithms else None,
        "authority_boundary": "verification_only",
    }
