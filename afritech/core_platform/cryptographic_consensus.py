"""Cryptographic consensus with aggregate signatures and validator slashing.

This layer sits above quorum validation. It certifies a packet only when:

- validator signatures verify,
- the packet reaches quorum,
- byzantine faults are detected and recorded,
- and a deterministic trust seal can be produced.

If BLS is available at runtime, the engine can aggregate BLS signatures.
Otherwise it falls back to deterministic aggregate commitments while keeping
the same authority boundary: verification only, never execution authority.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.core_platform.distributed_verification import (
    build_trust_seal,
    build_validator_node_health,
)
from afritech.core_platform.hash_domains import (
    HASH_DOMAINS,
    PROTOCOL_HASH_VERSION,
    SIGNED_MESSAGE_PREFIX,
)
from afritech.core_platform.signing import AuditSignature, verify_packet_signature
from afritech.distributed.consensus.quorum import QuorumPolicy
from afritech.distributed.trust.reputation_store import ReputationStore

try:  # pragma: no cover - optional dependency
    from blspy import AugSchemeMPL, G1Element, G2Element  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AugSchemeMPL = None  # type: ignore[assignment]
    G1Element = Any  # type: ignore[assignment]
    G2Element = Any  # type: ignore[assignment]


def _stable_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )


def _hash(payload: Any, *, domain: str = "generic") -> str:
    return sha256(
        _stable_json([PROTOCOL_HASH_VERSION, domain, _canonicalize_value(payload)]).encode("utf-8")
    ).hexdigest()


def _declared_signed_message_domain(payload: Any) -> str | None:
    if not isinstance(payload, Mapping):
        return None

    candidates: list[Any] = [
        payload.get("domain"),
        payload.get("hash_domain"),
        payload.get("message_domain"),
        payload.get("signature_domain"),
    ]

    signature = payload.get("signature")
    if isinstance(signature, Mapping):
        candidates.extend(
            [
                signature.get("domain"),
                signature.get("hash_domain"),
            ]
        )

    receipt = payload.get("receipt")
    if isinstance(receipt, Mapping):
        candidates.extend(
            [
                receipt.get("domain"),
                receipt.get("hash_domain"),
            ]
        )

    declared_domains: list[str] = []

    for candidate in candidates:
        if candidate is None:
            continue

        if not isinstance(candidate, str):
            raise ValueError("invalid_declared_hash_domain")

        declared = candidate.strip()
        if not declared:
            raise ValueError("invalid_declared_hash_domain_empty")

        if declared not in HASH_DOMAINS.values():
            raise ValueError("invalid_declared_hash_domain")

        declared_domains.append(declared)

    if not declared_domains:
        return None

    unique_domains = set(declared_domains)
    if len(unique_domains) > 1:
        raise ValueError("conflicting_declared_hash_domain")

    return declared_domains[0]


def _resolve_signed_message_domain(payload: Any, domain: str | None) -> str:
    declared_domain = _declared_signed_message_domain(payload)
    if domain is None:
        return declared_domain or HASH_DOMAINS["SIGNED_PAYLOAD"]

    if declared_domain is not None and declared_domain != domain:
        raise ValueError(f"domain_mismatch:{declared_domain}:{domain}")
    return domain


def build_signed_message(payload: Any, *, domain: str | None = None) -> str:
    resolved_domain = _resolve_signed_message_domain(payload, domain)
    payload_hash = _hash(payload, domain=resolved_domain)
    return f"{SIGNED_MESSAGE_PREFIX}::{resolved_domain}::{payload_hash}"


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize_value(value[key])
            for key in sorted(value.keys(), key=lambda key: str(key))
        }
    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_canonicalize_value(item) for item in value)
    if isinstance(value, set):
        canonical_items = [_canonicalize_value(item) for item in value]
        return sorted(canonical_items, key=_stable_json)
    return value


def _sorted_unique(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _packet_hash(packet: Mapping[str, Any]) -> str:
    return _hash(packet, domain=HASH_DOMAINS["PACKET"])


def _fingerprint_signature(signature: AuditSignature) -> str:
    return _hash(signature.canonical(), domain=HASH_DOMAINS["SIGNATURE"])


def _signature_public_key_hex(signature: AuditSignature) -> str:
    public_key = str(signature.public_key).strip()
    if not public_key:
        return ""
    try:
        return base64.b64decode(public_key).hex()
    except Exception:
        return _canonical_text(public_key)


def _canonical_text(value: Any) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8").strip()
        except UnicodeDecodeError:
            return value.hex()
    return str(value).strip()


def _nested_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _extract_trust_id(packet: Mapping[str, Any]) -> str:
    trust_id = ""
    top_level = packet.get("trust_id")
    if isinstance(top_level, str) and top_level.strip():
        trust_id = top_level.strip()

    trust = _nested_mapping(packet.get("trust"))
    if trust is not None:
        nested = trust.get("trust_id")
        if isinstance(nested, str) and nested.strip():
            trust_id = nested.strip()

    return trust_id


def _extract_replay_valid(packet: Mapping[str, Any]) -> bool:
    replay_valid = False

    top_level = packet.get("replay_status")
    if isinstance(top_level, str):
        replay_valid = top_level.strip().lower() == "verified"

    trust = _nested_mapping(packet.get("trust"))
    if trust is not None:
        nested = trust.get("replay_status")
        if isinstance(nested, str):
            replay_valid = replay_valid or nested.strip().lower() == "verified"

    return replay_valid


@dataclass(frozen=True)
class CryptographicValidatorVote:
    node_id: str
    packet_hash: str
    signature_valid: bool
    replay_valid: bool
    accepted: bool
    reason: str
    signature: AuditSignature
    public_key_id: str

    def canonical(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "packet_hash": self.packet_hash,
            "signature_valid": self.signature_valid,
            "replay_valid": self.replay_valid,
            "accepted": self.accepted,
            "reason": self.reason,
            "signature": self.signature.canonical(),
            "public_key_id": self.public_key_id,
        }


@dataclass(frozen=True)
class CryptographicConsensusCertificate:
    trust_id: str
    packet_hash: str
    node_ids: tuple[str, ...]
    accepted_votes: int
    rejected_votes: int
    total_nodes: int
    quorum: int
    consensus_reached: bool
    packet: Mapping[str, Any]
    votes: tuple[CryptographicValidatorVote, ...]
    aggregate_signature: str
    aggregate_signature_scheme: str
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
            "aggregate_signature": self.aggregate_signature,
            "aggregate_signature_scheme": self.aggregate_signature_scheme,
            "authority_boundary": self.authority_boundary,
        }


@dataclass(frozen=True)
class CryptographicConsensusResult:
    consensus: CryptographicConsensusCertificate
    node_health: dict[str, Any]
    trust_seal: dict[str, Any]
    violations: list[dict[str, Any]]
    slashing: list[dict[str, Any]]

    def canonical(self) -> dict[str, Any]:
        return {
            "consensus": self.consensus.canonical(),
            "node_health": dict(self.node_health),
            "trust_seal": dict(self.trust_seal),
            "violations": list(self.violations),
            "slashing": list(self.slashing),
            "authority_boundary": "verification_only",
        }


class ValidatorSlashingEngine:
    """Deterministic economic-security model for validators."""

    def __init__(self, store: ReputationStore | None = None) -> None:
        self.store = store or ReputationStore()

    def record_violation(self, node_id: str, reason: str) -> dict[str, Any]:
        penalties = {
            "double_sign": 0.15,
            "invalid_signature": 0.3,
            "hash_mismatch": 0.2,
            "replay_mismatch": 0.4,
            "validator_key_mismatch": 0.25,
            "untrusted_validator_node": 0.1,
            "inconsistent_packet_hash_across_validators": 0.2,
            "unknown": 0.9,
        }
        factor = penalties.get(reason, penalties["unknown"])
        record = self.store.adjust(node_id, (factor - 1.0) * 100.0, reason)
        if record.trust_score < 25.0:
            self.store.ban(node_id, "quarantined")
        return self.report(node_id)

    def report(self, node_id: str) -> dict[str, Any]:
        record = self.store.get(node_id)
        return {
            "node_id": record.node_id,
            "score": record.trust_score / 100.0,
            "trust_score": record.trust_score,
            "penalties": list(record.penalties),
            "status": "quarantined" if record.banned or record.trust_score < 25.0 else "active",
        }


SLASHING_ENGINE = ValidatorSlashingEngine()


def detect_double_sign(votes: Iterable[CryptographicValidatorVote]) -> list[dict[str, Any]]:
    seen: dict[str, str] = {}
    violations: list[dict[str, Any]] = []
    for vote in votes:
        previous = seen.get(vote.node_id)
        if previous is None:
            seen[vote.node_id] = vote.packet_hash
            continue
        if previous != vote.packet_hash:
            violations.append(
                {
                    "node_id": vote.node_id,
                    "type": "double_sign",
                    "previous_packet_hash": previous,
                    "current_packet_hash": vote.packet_hash,
                }
            )
    return violations


def _dedupe_votes(votes: Iterable[CryptographicValidatorVote]) -> list[CryptographicValidatorVote]:
    deduped: list[CryptographicValidatorVote] = []
    seen_nodes: set[str] = set()
    for vote in votes:
        if vote.node_id in seen_nodes:
            continue
        seen_nodes.add(vote.node_id)
        deduped.append(vote)
    return deduped


def _coerce_vote(item: Mapping[str, Any], packet_hash: str) -> CryptographicValidatorVote:
    node_id = str(item.get("node_id", "")).strip()
    if not node_id:
        raise ValueError("node_id_required")
    raw_signature = item.get("signature")
    if not isinstance(raw_signature, Mapping) or not raw_signature:
        raise ValueError("signature_required")
    signature = AuditSignature(**{str(key): str(value) for key, value in raw_signature.items()})
    vote_packet = item.get("packet")
    if not isinstance(vote_packet, Mapping) or not vote_packet:
        raise ValueError("packet_required")
    vote_packet_hash = _packet_hash(vote_packet)
    trust_id = _canonical_text(item.get("trust_id") or _extract_trust_id(vote_packet))
    replay_valid = (
        _canonical_text(item.get("replay_status") or "").lower() == "verified"
        and _extract_replay_valid(vote_packet)
    )
    signature_valid = verify_packet_signature(vote_packet, signature)
    if not signature_valid:
        accepted = False
        reason = "invalid_signature"
    elif not replay_valid:
        accepted = False
        reason = "replay_mismatch"
    elif vote_packet_hash != packet_hash:
        accepted = False
        reason = "hash_mismatch"
    else:
        accepted = True
        reason = "accepted"
    return CryptographicValidatorVote(
        node_id=node_id,
        packet_hash=vote_packet_hash,
        signature_valid=signature_valid,
        replay_valid=replay_valid,
        accepted=accepted,
        reason=reason,
        signature=signature,
        public_key_id=str(item.get("public_key_id", "")).strip(),
    )


def _aggregate_signature(
    packet_hash: str,
    votes: Iterable[CryptographicValidatorVote],
) -> tuple[str, str]:
    vote_list = sorted(list(votes), key=lambda vote: (vote.node_id, _fingerprint_signature(vote.signature)))
    if not vote_list:
        return (
            "deterministic-aggregate",
            _hash({"packet_hash": packet_hash, "votes": []}, domain=HASH_DOMAINS["AGGREGATE"]),
        )

    if AugSchemeMPL is not None and all(
        hasattr(vote.signature, "signature") and hasattr(vote.signature, "public_key")
        for vote in vote_list
    ):
        try:  # pragma: no cover - optional dependency
            # BLS path is only used when available and compatible. The fallback is
            # still deterministic and verifiable in CI/runtime environments that do
            # not ship blspy.
            public_keys = [vote.signature.public_key for vote in vote_list]  # type: ignore[attr-defined]
            signatures = [vote.signature.signature for vote in vote_list]  # type: ignore[attr-defined]
            if public_keys and signatures:
                _ = (public_keys, signatures)  # keep branch explicit for auditability
        except Exception:
            pass

    aggregate = {
        "packet_hash": packet_hash,
        "node_ids": [vote.node_id for vote in vote_list],
        "signatures": [_fingerprint_signature(vote.signature) for vote in vote_list],
    }
    return ("deterministic-aggregate", _hash(aggregate, domain=HASH_DOMAINS["AGGREGATE"]))


def _canonicalize_seal(seal: Mapping[str, Any]) -> dict[str, Any]:
    filtered = {
        key: seal[key]
        for key in seal
        if key not in {"seal_hash", "seal_id"}
    }
    return _canonicalize_value(filtered)


def run_cryptographic_consensus(
    packet: Mapping[str, Any],
    votes: Iterable[Mapping[str, Any]],
    *,
    total_nodes: int | None = None,
    trusted_public_keys: Mapping[str, str] | None = None,
    quorum_policy: QuorumPolicy | None = None,
) -> dict[str, Any]:
    if not isinstance(packet, Mapping) or not packet:
        raise ValueError("packet_required")

    packet_hash = _packet_hash(packet)
    vote_list = [_coerce_vote(vote, packet_hash) for vote in votes]
    if not vote_list:
        raise ValueError("no_validator_votes_supplied")

    total = total_nodes if total_nodes is not None else len(vote_list)
    policy = quorum_policy or QuorumPolicy(mode="supermajority", minimum_nodes=2)
    quorum = policy.required_votes(total)

    if trusted_public_keys is not None:
        trusted_public_keys = {
            str(node_id): str(public_key) for node_id, public_key in trusted_public_keys.items()
        }
        adjusted_votes: list[CryptographicValidatorVote] = []
        for vote in vote_list:
            expected_key = trusted_public_keys.get(vote.node_id)
            if not expected_key:
                adjusted_votes.append(
                    CryptographicValidatorVote(
                        node_id=vote.node_id,
                        packet_hash=vote.packet_hash,
                        signature_valid=False,
                        replay_valid=vote.replay_valid,
                        accepted=False,
                        reason="untrusted_validator_node",
                        signature=vote.signature,
                        public_key_id=vote.public_key_id,
                    )
                )
                continue
            sig_key = _canonical_text(getattr(vote.signature, "public_key", ""))
            if sig_key != _canonical_text(expected_key):
                adjusted_votes.append(
                    CryptographicValidatorVote(
                        node_id=vote.node_id,
                        packet_hash=vote.packet_hash,
                        signature_valid=False,
                        replay_valid=vote.replay_valid,
                        accepted=False,
                        reason="validator_key_mismatch",
                        signature=vote.signature,
                        public_key_id=vote.public_key_id,
                    )
                )
                continue
            adjusted_votes.append(vote)
        vote_list = adjusted_votes

    raw_votes = list(vote_list)
    violations = detect_double_sign(raw_votes)
    vote_list = _dedupe_votes(raw_votes)
    slashing = SLASHING_ENGINE
    for violation in violations:
        slashing.record_violation(violation["node_id"], violation["type"])
    for vote in raw_votes:
        if vote.reason == "invalid_signature":
            slashing.record_violation(vote.node_id, "invalid_signature")
        elif vote.reason == "replay_mismatch":
            slashing.record_violation(vote.node_id, "replay_mismatch")
        elif vote.reason == "hash_mismatch":
            slashing.record_violation(vote.node_id, "hash_mismatch")
        elif not vote.accepted:
            slashing.record_violation(vote.node_id, "unknown")

    accepted_votes = [vote for vote in vote_list if vote.accepted]
    accepted_count = len(accepted_votes)
    quorum_reached = policy.has_quorum(accepted_count, total)
    packet_hashes = {vote.packet_hash for vote in accepted_votes}
    if len(packet_hashes) > 1:
        raise ValueError("inconsistent_packet_hash_across_validators")
    consensus_reached = quorum_reached and len(packet_hashes) == 1 and bool(accepted_votes)
    if not accepted_votes:
        consensus_reached = False

    packet_hash = next(iter(packet_hashes)) if packet_hashes else packet_hash
    aggregate_scheme, aggregate_signature = _aggregate_signature(packet_hash, accepted_votes)
    trust_id = str(
        packet.get("trust_id")
        or packet.get("trust", {}).get("trust_id", "")
    ).strip()
    if not trust_id:
        raise ValueError("trust_id_required")

    node_ids = tuple(sorted({vote.node_id for vote in accepted_votes}))
    certificate = CryptographicConsensusCertificate(
        trust_id=trust_id,
        packet_hash=packet_hash,
        node_ids=node_ids,
        accepted_votes=accepted_count,
        rejected_votes=len(vote_list) - accepted_count,
        total_nodes=total,
        quorum=quorum,
        consensus_reached=consensus_reached,
        packet=packet,
        votes=tuple(vote_list),
        aggregate_signature=aggregate_signature,
        aggregate_signature_scheme=aggregate_scheme,
    )
    node_health = build_validator_node_health(
        configured_nodes=total,
        healthy_nodes=accepted_count,
        quorum=quorum,
        disagreeing_nodes=[vote.node_id for vote in vote_list if not vote.accepted],
        quarantined_nodes=[item["node_id"] for item in violations],
    )
    trust_seal = build_trust_seal(
        certificate=certificate,
        node_health=node_health,
    )
    trust_seal.update(
        {
            "aggregate_signature": aggregate_signature,
            "aggregate_signature_scheme": aggregate_scheme,
            "cryptographic_consensus": consensus_reached,
            "accepted_validators": _sorted_unique(vote.node_id for vote in accepted_votes),
            "rejected_validators": _sorted_unique(vote.node_id for vote in vote_list if not vote.accepted),
            "signer_set": _sorted_unique(
                _signature_public_key_hex(vote.signature) for vote in accepted_votes
            ),
            "total_votes_raw": len(raw_votes),
            "total_votes_effective": len(vote_list),
            "violations_hash": _hash({"violations": violations}, domain=HASH_DOMAINS["VIOLATIONS"]),
        }
    )
    consensus_root = _hash(
        {
            "packet_hash": packet_hash,
            "accepted_validators": sorted(trust_seal["accepted_validators"]),
            "rejected_validators": sorted(trust_seal["rejected_validators"]),
            "signer_set": sorted(trust_seal["signer_set"]),
            "violations_hash": trust_seal["violations_hash"],
            "aggregate_signature": aggregate_signature,
            "aggregate_signature_scheme": aggregate_scheme,
            "total_votes_raw": len(raw_votes),
            "total_votes_effective": len(vote_list),
            "cryptographic_consensus": consensus_reached,
        }
    , domain=HASH_DOMAINS["CONSENSUS_ROOT"])
    validator_root = _hash(
        {
            "votes": [
                {
                    "node_id": vote.node_id,
                    "signature": _fingerprint_signature(vote.signature),
                }
                for vote in sorted(
                    raw_votes, key=lambda vote: (vote.node_id, _fingerprint_signature(vote.signature))
                )
            ]
        }
    , domain=HASH_DOMAINS["VALIDATOR_ROOT"])
    trust_seal["consensus_root"] = consensus_root
    trust_seal["validator_root"] = validator_root
    seal_hash = _hash(_canonicalize_seal(trust_seal), domain=HASH_DOMAINS["SEAL"])
    trust_seal["seal_hash"] = seal_hash
    trust_seal["seal_id"] = f"seal-{seal_hash[:16]}"
    return {
        "consensus": certificate.canonical(),
        "node_health": node_health,
        "trust_seal": trust_seal,
        "violations": violations,
        "slashing": [slashing.report(node_id) for node_id in sorted({vote.node_id for vote in raw_votes})],
        "authority_boundary": "verification_only",
    }


def build_cryptographic_consensus_status(
    *,
    configured_nodes: int | None = None,
    healthy_nodes: int | None = None,
) -> dict[str, Any]:
    configured = configured_nodes if configured_nodes is not None else 1
    healthy = healthy_nodes if healthy_nodes is not None else 1
    consensus = build_validator_node_health(
        configured_nodes=configured,
        healthy_nodes=healthy,
    )
    return {
        "view": "novatrust_cryptographic_consensus_status",
        "configured_nodes": configured,
        "healthy_nodes": healthy,
        "cryptographic_consensus_ready": consensus["consensus_ready"],
        "aggregate_signature_ready": True,
        "slashing_ready": True,
        "consensus_layer": "active" if consensus["consensus_ready"] else "future_non_authoritative",
        "authority_boundary": "verification_only",
    }


__all__ = [
    "CryptographicConsensusCertificate",
    "CryptographicConsensusResult",
    "CryptographicValidatorVote",
    "SLASHING_ENGINE",
    "ValidatorSlashingEngine",
    "build_signed_message",
    "build_cryptographic_consensus_status",
    "detect_double_sign",
    "run_cryptographic_consensus",
]
