"""Signed trust-node import and federation protocol.

Federation verifies and stores evidence. It never grants payment, settlement,
policy, or runtime execution authority.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from afritech.core_platform.signing import AuditSignature, verify_packet_signature


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TrustNodeEnvelope:
    node_id: str
    packet: Mapping[str, Any]
    signature: Mapping[str, str]
    protocol_version: str = "novatrust-node-v1"
    propagated_at: str | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TrustNodeEnvelope":
        packet = payload.get("packet")
        signature = payload.get("signature")
        node_id = str(payload.get("node_id", "")).strip()
        if not node_id:
            raise ValueError("node_id_required")
        if not isinstance(packet, Mapping) or not packet:
            raise ValueError("non_empty_packet_required")
        if not isinstance(signature, Mapping) or not signature:
            raise ValueError("signature_required")
        return cls(
            node_id=node_id,
            packet=dict(packet),
            signature={str(key): str(value) for key, value in signature.items()},
            protocol_version=str(payload.get("protocol_version", "novatrust-node-v1")),
            propagated_at=(
                str(payload["propagated_at"]) if payload.get("propagated_at") else None
            ),
        )

    @property
    def envelope_id(self) -> str:
        return _canonical_hash(
            {
                "node_id": self.node_id,
                "packet": self.packet,
                "signature": self.signature,
                "protocol_version": self.protocol_version,
            }
        )


@dataclass(frozen=True)
class TrustImportResult:
    status: str
    trust_id: str
    source_node: str
    envelope_id: str
    signature_valid: bool
    imported: bool
    authority_boundary: str = "verification_only"

    def canonical(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "trust_id": self.trust_id,
            "source_node": self.source_node,
            "envelope_id": self.envelope_id,
            "signature_valid": self.signature_valid,
            "imported": self.imported,
            "authority_boundary": self.authority_boundary,
        }


class TrustImportStore(Protocol):
    def save_imported_packet(
        self,
        *,
        trust_id: str,
        packet: Mapping[str, Any],
        signature: Mapping[str, str],
        source_node: str,
        envelope_id: str,
        imported_at: str,
    ) -> bool:
        """Persist an imported packet and return True only for a new import."""


def import_trust_envelope(
    envelope: TrustNodeEnvelope,
    *,
    store: TrustImportStore,
    trusted_public_keys: Mapping[str, str] | None = None,
) -> TrustImportResult:
    try:
        signature = AuditSignature(**dict(envelope.signature))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_signature_contract") from exc

    if trusted_public_keys is not None:
        expected_key = trusted_public_keys.get(envelope.node_id)
        if not expected_key:
            raise ValueError("untrusted_source_node")
        if signature.public_key != expected_key:
            raise ValueError("source_node_key_mismatch")

    if not verify_packet_signature(envelope.packet, signature):
        raise ValueError("signature_verification_failed")

    trust = envelope.packet.get("trust")
    if not isinstance(trust, Mapping):
        raise ValueError("trust_packet_required")
    trust_id = str(trust.get("trust_id", "")).strip()
    if not trust_id:
        raise ValueError("trust_id_required")

    imported_at = datetime.now(timezone.utc).isoformat()
    created = store.save_imported_packet(
        trust_id=trust_id,
        packet=envelope.packet,
        signature=envelope.signature,
        source_node=envelope.node_id,
        envelope_id=envelope.envelope_id,
        imported_at=imported_at,
    )
    return TrustImportResult(
        status="imported" if created else "already_imported",
        trust_id=trust_id,
        source_node=envelope.node_id,
        envelope_id=envelope.envelope_id,
        signature_valid=True,
        imported=created,
    )


def federation_readiness(*, configured_nodes: int, healthy_nodes: int) -> dict[str, Any]:
    federation_ready = configured_nodes >= 2 and healthy_nodes >= 2
    return {
        "import_layer": "ready",
        "federation_layer": "ready" if federation_ready else "configuration_required",
        "consensus_layer": "future_non_authoritative",
        "configured_nodes": configured_nodes,
        "healthy_nodes": healthy_nodes,
        "federation_ready": federation_ready,
        "multi_node_consensus_ready": False,
        "authority_boundary": (
            "Federation and consensus observations cannot authorize payments, "
            "settlement, policy overrides, or runtime mutation."
        ),
    }


def build_trust_node_network_status(
    *,
    configured_nodes: int | None = None,
    healthy_nodes: int | None = None,
) -> dict[str, Any]:
    configured = configured_nodes if configured_nodes is not None else int(os.environ.get("NOVATRUST_FEDERATION_NODES", "1"))
    healthy = healthy_nodes if healthy_nodes is not None else int(os.environ.get("NOVATRUST_FEDERATION_HEALTHY_NODES", "1"))
    validator_quorum = max(2, configured // 2 + 1) if configured > 0 else 1
    from afritech.platform_contracts.federation import local_federation_manifest

    return {
        "view": "novatrust_trust_node_network_status",
        "configured_nodes": configured,
        "healthy_nodes": healthy,
        "validator_quorum": validator_quorum,
        "import_layer": "ready" if healthy >= 1 else "configuration_required",
        "federation_layer": "ready" if configured >= 2 and healthy >= 2 else "configuration_required",
        "distributed_validation_ready": configured >= 3 and healthy >= validator_quorum,
        "consensus_layer": "future_non_authoritative",
        "event_bus_backend": os.environ.get("NOVAPAY_EVENT_BUS_BACKEND", "in_memory"),
        "event_bus_brokers_configured": bool(os.environ.get("NOVAPAY_EVENT_BUS_KAFKA_BROKERS", "")),
        "compatibility_manifest": local_federation_manifest().canonical(),
        "authority_boundary": (
            "Federation and consensus observations cannot authorize payments, "
            "settlement, policy overrides, or runtime mutation."
        ),
    }


__all__ = [
    "TrustImportResult",
    "TrustNodeEnvelope",
    "federation_readiness",
    "import_trust_envelope",
    "build_trust_node_network_status",
]
