"""Distributed verification utilities for validator quorum and trust sealing.

The distributed verification layer certifies evidence produced by multiple
independent validators. It is explicitly verification-only: it can attest to
quorum, health, and seal integrity, but it cannot authorize execution,
settlement, or policy overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.core_platform.consensus import (
    ValidatorConsensusCertificate,
    ValidatorConsensusEngine,
)
from afritech.distributed.consensus.quorum import QuorumPolicy


def _stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )


def _hash(payload: Mapping[str, Any]) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _sorted_unique(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


@dataclass(frozen=True)
class DistributedVerificationResult:
    consensus: ValidatorConsensusCertificate
    trust_seal: dict[str, Any]
    node_health: dict[str, Any]

    def canonical(self) -> dict[str, Any]:
        return {
            "consensus": self.consensus.canonical(),
            "trust_seal": dict(self.trust_seal),
            "node_health": dict(self.node_health),
            "authority_boundary": "verification_only",
        }


def build_validator_node_health(
    *,
    configured_nodes: int,
    healthy_nodes: int,
    quorum: int | None = None,
    disagreeing_nodes: Iterable[str] | None = None,
    quarantined_nodes: Iterable[str] | None = None,
) -> dict[str, Any]:
    if configured_nodes < 0:
        raise ValueError("configured_nodes must be non-negative")
    if healthy_nodes < 0:
        raise ValueError("healthy_nodes must be non-negative")

    policy = QuorumPolicy(mode="supermajority", minimum_nodes=2)
    validator_quorum = (
        quorum
        if quorum is not None
        else (2 if configured_nodes < 2 else policy.required_votes(configured_nodes))
    )
    disagreeing = _sorted_unique(disagreeing_nodes)
    quarantined = _sorted_unique(quarantined_nodes)
    agreement_ratio = round(healthy_nodes / configured_nodes, 4) if configured_nodes else 0.0
    disagreement_ratio = round(len(disagreeing) / configured_nodes, 4) if configured_nodes else 0.0

    if configured_nodes == 0:
        status = "unavailable"
    elif quarantined:
        status = "quarantined"
    elif healthy_nodes >= validator_quorum and not disagreeing:
        status = "healthy"
    elif healthy_nodes >= validator_quorum:
        status = "degraded"
    else:
        status = "critical"

    consensus_ready = configured_nodes >= 3 and healthy_nodes >= validator_quorum and not quarantined
    health_score = max(
        0,
        min(
            100,
            int(
                round(
                    100
                    * (
                        (agreement_ratio * 0.7)
                        + (max(0.0, 1.0 - disagreement_ratio) * 0.3)
                    )
                )
            ),
        ),
    )

    health_payload = {
        "configured_nodes": configured_nodes,
        "healthy_nodes": healthy_nodes,
        "validator_quorum": validator_quorum,
        "agreement_ratio": agreement_ratio,
        "disagreement_ratio": disagreement_ratio,
        "disagreeing_nodes": disagreeing,
        "quarantined_nodes": quarantined,
        "consensus_ready": consensus_ready,
        "status": status,
        "health_score": health_score,
        "authority_boundary": "verification_only",
    }
    health_payload["health_hash"] = _hash(health_payload)
    return health_payload


def build_trust_seal(
    *,
    certificate: ValidatorConsensusCertificate | Mapping[str, Any] | Any,
    node_health: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(certificate, ValidatorConsensusCertificate):
        certificate_payload = certificate.canonical()
    elif hasattr(certificate, "canonical"):
        certificate_payload = certificate.canonical()
    else:
        certificate_payload = dict(certificate)
    node_ids = _sorted_unique(certificate_payload.get("node_ids"))
    accepted_votes = int(certificate_payload.get("accepted_votes", len(node_ids)))
    rejected_votes = int(certificate_payload.get("rejected_votes", 0))
    total_nodes = int(certificate_payload.get("total_nodes", max(1, len(node_ids))))
    quorum = int(certificate_payload.get("quorum", max(1, len(node_ids))))
    trust_id = str(certificate_payload.get("trust_id", "")).strip()
    packet_hash = str(certificate_payload.get("packet_hash", "")).strip()
    if not trust_id:
        raise ValueError("trust_id_required")
    if not packet_hash:
        raise ValueError("packet_hash_required")

    seal_payload = {
        "trust_id": trust_id,
        "packet_hash": packet_hash,
        "node_ids": node_ids,
        "accepted_votes": accepted_votes,
        "rejected_votes": rejected_votes,
        "total_nodes": total_nodes,
        "quorum": quorum,
        "consensus_reached": bool(certificate_payload.get("consensus_reached", False)),
        "authority_boundary": "verification_only",
    }
    if node_health is not None:
        seal_payload["node_health_hash"] = str(node_health.get("health_hash", ""))
        seal_payload["node_health_status"] = str(node_health.get("status", "unknown"))

    seal_hash = _hash(seal_payload)
    return {
        "seal_id": f"seal-{seal_hash[:16]}",
        "seal_hash": seal_hash,
        "trust_id": trust_id,
        "packet_hash": packet_hash,
        "node_ids": node_ids,
        "accepted_votes": accepted_votes,
        "rejected_votes": rejected_votes,
        "total_nodes": total_nodes,
        "quorum": quorum,
        "agreement_ratio": round(
            accepted_votes / max(1, accepted_votes + rejected_votes), 4
        ),
        "consensus_reached": bool(certificate_payload.get("consensus_reached", False)),
        "authority_boundary": "verification_only",
        "node_health_hash": (node_health or {}).get("health_hash"),
        "node_health_status": (node_health or {}).get("status", "unknown"),
    }


def validate_distributed_consensus(
    *,
    packet: Mapping[str, Any],
    validators: Iterable[Mapping[str, Any]],
    total_nodes: int | None = None,
    trusted_public_keys: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(packet, Mapping) or not packet:
        raise ValueError("packet_required")

    engine = ValidatorConsensusEngine(
        trusted_public_keys=trusted_public_keys,
        require_replay=True,
    )
    certificate = engine.decide(validators, total_nodes=total_nodes)
    disagreeing_nodes = [
        vote.node_id for vote in certificate.votes if not vote.accepted
    ]
    node_health = build_validator_node_health(
        configured_nodes=certificate.total_nodes,
        healthy_nodes=certificate.accepted_votes,
        quorum=certificate.quorum,
        disagreeing_nodes=disagreeing_nodes,
        quarantined_nodes=disagreeing_nodes,
    )
    trust_seal = build_trust_seal(
        certificate=certificate,
        node_health=node_health,
    )
    return {
        "consensus": certificate.canonical(),
        "node_health": node_health,
        "trust_seal": trust_seal,
        "authority_boundary": "verification_only",
        "packet_hash": certificate.packet_hash,
        "trust_id": certificate.trust_id,
        "consensus_reached": certificate.consensus_reached,
    }


__all__ = [
    "DistributedVerificationResult",
    "build_trust_seal",
    "build_validator_node_health",
    "validate_distributed_consensus",
]
