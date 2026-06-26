"""Validator quorum consensus for NovaPay trust evidence.

The consensus layer certifies evidence produced by validator nodes. It does not
authorize payment execution, settlement, or policy overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from typing import Any, Iterable, Mapping

from afritech.core_platform.signing import (
    AuditSignature,
    signing_key_ready,
    verify_packet_signature,
)
from afritech.distributed.consensus.quorum import QuorumPolicy


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class ValidatorConsensusEnvelope:
    node_id: str
    packet: Mapping[str, Any]
    signature: Mapping[str, str]
    protocol_version: str = "novatrust-validator-v1"
    observed_at: str | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ValidatorConsensusEnvelope":
        node_id = str(payload.get("node_id", "")).strip()
        packet = payload.get("packet")
        signature = payload.get("signature")
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
            protocol_version=str(payload.get("protocol_version", "novatrust-validator-v1")),
            observed_at=(
                str(payload["observed_at"]) if payload.get("observed_at") else None
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
class ValidatorConsensusVote:
    node_id: str
    trust_id: str
    packet_hash: str
    signature_valid: bool
    replay_valid: bool
    accepted: bool
    reason: str
    envelope_id: str

    def canonical(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "trust_id": self.trust_id,
            "packet_hash": self.packet_hash,
            "signature_valid": self.signature_valid,
            "replay_valid": self.replay_valid,
            "accepted": self.accepted,
            "reason": self.reason,
            "envelope_id": self.envelope_id,
        }


@dataclass(frozen=True)
class ValidatorConsensusCertificate:
    trust_id: str
    packet_hash: str
    node_ids: tuple[str, ...]
    accepted_votes: int
    rejected_votes: int
    total_nodes: int
    quorum: int
    consensus_reached: bool
    packet: Mapping[str, Any]
    votes: tuple[ValidatorConsensusVote, ...]
    authority_boundary: str = "verification_only"

    def canonical(self) -> dict[str, Any]:
        return {
            "trust_id": self.trust_id,
            "packet_hash": self.packet_hash,
            "node_ids": list(self.node_ids),
            "accepted_votes": self.accepted_votes,
            "rejected_votes": self.rejected_votes,
            "total_nodes": self.total_nodes,
            "quorum": self.quorum,
            "consensus_reached": self.consensus_reached,
            "packet": dict(self.packet),
            "votes": [vote.canonical() for vote in self.votes],
            "authority_boundary": self.authority_boundary,
        }


class ValidatorConsensusError(RuntimeError):
    """Raised when validator quorum consensus cannot be formed."""


class ValidatorConsensusConflictError(ValidatorConsensusError):
    """Raised when validators attest to conflicting packet hashes."""


class ValidatorConsensusEngine:
    """Deterministic validator quorum over trust packets."""

    def __init__(
        self,
        *,
        quorum_policy: QuorumPolicy | None = None,
        trusted_public_keys: Mapping[str, str] | None = None,
        require_replay: bool = True,
    ) -> None:
        self.quorum_policy = quorum_policy or QuorumPolicy(mode="majority", minimum_nodes=2)
        self.trusted_public_keys = dict(trusted_public_keys or {})
        self.require_replay = require_replay

    def decide(
        self,
        envelopes: Iterable[ValidatorConsensusEnvelope | Mapping[str, Any]],
        *,
        total_nodes: int | None = None,
    ) -> ValidatorConsensusCertificate:
        envelope_list = [self._coerce_envelope(item) for item in envelopes]
        if not envelope_list:
            raise ValidatorConsensusError("no_validator_envelopes_supplied")

        total = total_nodes if total_nodes is not None else len(envelope_list)
        quorum = self.quorum_policy.required_votes(total)

        votes: list[ValidatorConsensusVote] = []
        for envelope in envelope_list:
            votes.append(self._vote(envelope))

        deduped_votes: list[ValidatorConsensusVote] = []
        seen_votes: set[tuple[str, str]] = set()
        for vote in votes:
            key = (vote.node_id, vote.packet_hash)
            if key in seen_votes:
                continue
            seen_votes.add(key)
            deduped_votes.append(vote)

        accepted_votes = [vote for vote in deduped_votes if vote.accepted]
        if not accepted_votes:
            raise ValidatorConsensusError("no_valid_validator_votes")

        packet_hashes = {vote.packet_hash for vote in accepted_votes}
        if len(packet_hashes) > 1:
            raise ValidatorConsensusConflictError("conflicting_validator_packet_hashes")

        packet_hash = next(iter(packet_hashes))
        trust_id = accepted_votes[0].trust_id
        if not trust_id:
            raise ValidatorConsensusError("trust_id_required")

        accepted_count = len(accepted_votes)
        if not self.quorum_policy.has_quorum(accepted_count, total):
            raise ValidatorConsensusError(
                f"quorum_not_reached: votes={accepted_count} required={quorum}"
            )

        original_packet = envelope_list[0].packet

        return ValidatorConsensusCertificate(
            trust_id=trust_id,
            packet_hash=packet_hash,
            node_ids=tuple(sorted({vote.node_id for vote in accepted_votes})),
            accepted_votes=accepted_count,
            rejected_votes=len(deduped_votes) - accepted_count,
            total_nodes=total,
            quorum=quorum,
            consensus_reached=True,
            packet=original_packet,
            votes=tuple(deduped_votes),
        )

    def _coerce_envelope(
        self,
        envelope: ValidatorConsensusEnvelope | Mapping[str, Any],
    ) -> ValidatorConsensusEnvelope:
        if isinstance(envelope, ValidatorConsensusEnvelope):
            return envelope
        if not isinstance(envelope, Mapping):
            raise TypeError("validator consensus envelope must be a mapping")
        return ValidatorConsensusEnvelope.from_payload(envelope)

    def _vote(self, envelope: ValidatorConsensusEnvelope) -> ValidatorConsensusVote:
        trust_id, replay_valid = self._extract_trust_state(envelope.packet)
        packet_hash = _canonical_hash(envelope.packet)

        try:
            signature = AuditSignature(**dict(envelope.signature))
        except (TypeError, ValueError):
            return ValidatorConsensusVote(
                node_id=envelope.node_id,
                trust_id=trust_id,
                packet_hash=packet_hash,
                signature_valid=False,
                replay_valid=replay_valid,
                accepted=False,
                reason="invalid_signature_contract",
                envelope_id=envelope.envelope_id,
            )

        signature_valid = verify_packet_signature(envelope.packet, signature)

        if self.trusted_public_keys:
            expected_key = self.trusted_public_keys.get(envelope.node_id)
            if not expected_key:
                return ValidatorConsensusVote(
                    node_id=envelope.node_id,
                    trust_id=trust_id,
                    packet_hash=packet_hash,
                    signature_valid=False,
                    replay_valid=replay_valid,
                    accepted=False,
                    reason="untrusted_validator_node",
                    envelope_id=envelope.envelope_id,
                )
            if signature.public_key != expected_key:
                return ValidatorConsensusVote(
                    node_id=envelope.node_id,
                    trust_id=trust_id,
                    packet_hash=packet_hash,
                    signature_valid=False,
                    replay_valid=replay_valid,
                    accepted=False,
                    reason="validator_key_mismatch",
                    envelope_id=envelope.envelope_id,
                )

        if self.require_replay and not replay_valid:
            return ValidatorConsensusVote(
                node_id=envelope.node_id,
                trust_id=trust_id,
                packet_hash=packet_hash,
                signature_valid=signature_valid,
                replay_valid=False,
                accepted=False,
                reason="replay_not_verified",
                envelope_id=envelope.envelope_id,
            )

        accepted = signature_valid and replay_valid
        reason = "accepted" if accepted else "signature_verification_failed"
        return ValidatorConsensusVote(
            node_id=envelope.node_id,
            trust_id=trust_id,
            packet_hash=packet_hash,
            signature_valid=signature_valid,
            replay_valid=replay_valid,
            accepted=accepted,
            reason=reason,
            envelope_id=envelope.envelope_id,
        )

    @staticmethod
    def _extract_trust_state(packet: Mapping[str, Any]) -> tuple[str, bool]:
        trust_id = ""
        replay_valid = False

        top_level_trust_id = packet.get("trust_id")
        if isinstance(top_level_trust_id, str) and top_level_trust_id.strip():
            trust_id = top_level_trust_id.strip()

        top_level_replay = packet.get("replay_status")
        if isinstance(top_level_replay, str):
            replay_valid = top_level_replay == "verified"

        trust = packet.get("trust")
        if isinstance(trust, Mapping):
            nested_trust_id = trust.get("trust_id")
            if isinstance(nested_trust_id, str) and nested_trust_id.strip():
                trust_id = nested_trust_id.strip()
            nested_replay = trust.get("replay_status")
            if isinstance(nested_replay, str):
                replay_valid = replay_valid or nested_replay == "verified"

        return trust_id, replay_valid


def build_validator_consensus_status(
    *,
    configured_nodes: int | None = None,
    healthy_nodes: int | None = None,
) -> dict[str, Any]:
    configured = (
        configured_nodes
        if configured_nodes is not None
        else int(os.environ.get("NOVATRUST_FEDERATION_NODES", "1"))
    )
    healthy = (
        healthy_nodes
        if healthy_nodes is not None
        else int(os.environ.get("NOVATRUST_FEDERATION_HEALTHY_NODES", "1"))
    )
    enabled = _env_bool("NOVATRUST_CONSENSUS_ENABLED")
    quorum_policy = QuorumPolicy(
        mode=os.environ.get("NOVATRUST_CONSENSUS_MODE", "majority"),
        minimum_nodes=2,
    )
    quorum = quorum_policy.required_votes(configured) if configured >= 2 else 2
    signing_ready = signing_key_ready()
    ready = enabled and configured >= 3 and healthy >= quorum and signing_ready
    return {
        "view": "novatrust_validator_consensus_status",
        "consensus_enabled": enabled,
        "consensus_mode": quorum_policy.mode,
        "configured_nodes": configured,
        "healthy_nodes": healthy,
        "validator_quorum": quorum,
        "signing_ready": signing_ready,
        "consensus_layer": "active" if ready else "future_non_authoritative",
        "multi_node_consensus_ready": ready,
        "authority_boundary": (
            "Validator quorum can certify evidence but cannot authorize payments, "
            "settlement, policy overrides, or runtime mutation."
        ),
    }


__all__ = [
    "ValidatorConsensusCertificate",
    "ValidatorConsensusEngine",
    "ValidatorConsensusEnvelope",
    "ValidatorConsensusError",
    "ValidatorConsensusConflictError",
    "ValidatorConsensusVote",
    "build_validator_consensus_status",
]
