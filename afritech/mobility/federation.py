"""Federated mobility infrastructure for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ecosystems.afriride.geo.types import GeoPoint

from afritech.identity.mobility_participant import MobilityParticipant, validate_mobility_participant
from afritech.mobility.trust_dispatch import DispatchCandidate
from afritech.mobility.trust_network import TrustProfile


SCHEMA = "afritech.mobility.federation_state.v1"
AUTHORITY_BOUNDARY = "federation_reference_only"

ALLOWED_FEDERATION_STATUSES = ("pending", "verified", "suspended")
ALLOWED_CERTIFICATION_STATUSES = ("pending", "verified", "suspended")
ALLOWED_UNIT_TYPES = ("fleet", "merchant", "institution")
ALLOWED_VERIFICATION_LEVELS = ("verified", "pending", "provisional", "restricted")

VERIFICATION_FACTORS = {
    "verified": 1.0,
    "pending": 0.82,
    "provisional": 0.65,
    "restricted": 0.0,
}


class FederationError(ValueError):
    """Raised when federation payloads or state are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FederationError(f"{label} is required")
    return value.strip()


def _require_hash(value: object, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64:
        raise FederationError(f"{label} must be a 64-character hex digest")
    return value


def _require_number(value: object, label: str, *, minimum: float, maximum: float) -> float:
    if not isinstance(value, (int, float)):
        raise FederationError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise FederationError(f"{label} must be between {minimum} and {maximum}")
    return round(number, 6)


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or value < minimum:
        raise FederationError(f"{label} must be an integer >= {minimum}")
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise FederationError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _normalize_text_tuple(values: Iterable[object], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise FederationError(f"{label} must be iterable")
    normalized = tuple(_require_text(value, label[:-1] if label.endswith("s") else label) for value in values)
    return tuple(sorted(set(normalized)))


def derive_federated_trust(
    local_trust_score: float,
    federation_weight: float,
    verification_level: str,
) -> float:
    local = _require_number(local_trust_score, "local_trust_score", minimum=0.0, maximum=100.0)
    weight = _require_number(federation_weight, "federation_weight", minimum=0.0, maximum=1.0)
    if verification_level not in VERIFICATION_FACTORS:
        raise FederationError(f"unsupported verification_level: {verification_level}")
    factor = VERIFICATION_FACTORS[verification_level]
    derived = round(min(local, local * weight * factor), 6)
    return max(0.0, min(100.0, derived))


def _participants_for_transition(transitions: tuple["FederationTransition", ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for transition in transitions:
        counts[transition.participant_id] = counts.get(transition.participant_id, 0) + 1
    return counts


@dataclass(frozen=True)
class FederationTransition:
    transition_id: str
    participant_id: str
    from_network: str
    to_network: str
    trust_transferred: float
    verification_level: str
    source_operation_id: str
    evidence_link: str
    timestamp: int
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_id", _require_text(self.transition_id, "transition_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "from_network", _require_text(self.from_network, "from_network"))
        object.__setattr__(self, "to_network", _require_text(self.to_network, "to_network"))
        if self.from_network == self.to_network:
            raise FederationError("from_network and to_network must differ")
        object.__setattr__(self, "trust_transferred", _require_number(self.trust_transferred, "trust_transferred", minimum=0.0, maximum=100.0))
        if self.verification_level not in VERIFICATION_FACTORS:
            raise FederationError(f"unsupported verification_level: {self.verification_level}")
        object.__setattr__(self, "source_operation_id", _require_text(self.source_operation_id, "source_operation_id"))
        object.__setattr__(self, "evidence_link", _require_text(self.evidence_link, "evidence_link"))
        if not isinstance(self.timestamp, int):
            raise FederationError("timestamp must be an integer")
        if not isinstance(self.verified, bool) or not self.verified:
            raise FederationError("federation transitions must be verified")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FederationTransition":
        if not isinstance(payload, Mapping):
            raise FederationError("federation transition payload must be a mapping")
        return cls(
            transition_id=_require_text(payload.get("transition_id") or payload.get("id"), "transition_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            from_network=_require_text(payload.get("from_network"), "from_network"),
            to_network=_require_text(payload.get("to_network"), "to_network"),
            trust_transferred=float(payload.get("trust_transferred", 0.0)),
            verification_level=_require_text(payload.get("verification_level"), "verification_level"),
            source_operation_id=_require_text(payload.get("source_operation_id"), "source_operation_id"),
            evidence_link=_require_text(payload.get("evidence_link"), "evidence_link"),
            timestamp=int(payload.get("timestamp", 0)),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_link": self.evidence_link,
            "from_network": self.from_network,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "source_operation_id": self.source_operation_id,
            "timestamp": self.timestamp,
            "to_network": self.to_network,
            "transition_hash": self.transition_hash,
            "transition_id": self.transition_id,
            "trust_transferred": round(self.trust_transferred, 6),
            "verification_level": self.verification_level,
            "verified": self.verified,
        }

    @property
    def transition_hash(self) -> str:
        payload = {
            "evidence_link": self.evidence_link,
            "from_network": self.from_network,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "source_operation_id": self.source_operation_id,
            "timestamp": self.timestamp,
            "to_network": self.to_network,
            "transition_id": self.transition_id,
            "trust_transferred": round(self.trust_transferred, 6),
            "verification_level": self.verification_level,
            "verified": self.verified,
        }
        return _canonical_hash(payload)


@dataclass(frozen=True)
class FederatedParticipant:
    participant_id: str
    home_network: str
    roles: tuple[str, ...]
    trust_profile: TrustProfile
    federation_status: str
    federation_weight: float = 0.85
    verification_level: str = "verified"
    cross_network_events: int = 0
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "home_network", _require_text(self.home_network, "home_network"))
        if isinstance(self.roles, (str, bytes)) or not isinstance(self.roles, Iterable):
            raise FederationError("roles must be iterable")
        roles = tuple(_require_text(role, "role") for role in self.roles)
        if not roles:
            raise FederationError("at least one role is required")
        object.__setattr__(self, "roles", tuple(sorted(set(roles))))
        if not isinstance(self.trust_profile, TrustProfile):
            raise FederationError("trust_profile must be a TrustProfile")
        if self.trust_profile.participant_id != self.participant_id:
            raise FederationError("trust_profile participant_id mismatch")
        if self.federation_status not in ALLOWED_FEDERATION_STATUSES:
            raise FederationError(f"unsupported federation_status: {self.federation_status}")
        object.__setattr__(self, "federation_weight", _require_number(self.federation_weight, "federation_weight", minimum=0.0, maximum=1.0))
        if self.verification_level not in VERIFICATION_FACTORS:
            raise FederationError(f"unsupported verification_level: {self.verification_level}")
        object.__setattr__(self, "cross_network_events", _require_int(self.cross_network_events, "cross_network_events"))
        object.__setattr__(self, "evidence_links", tuple(sorted(set(_normalize_text_tuple(self.evidence_links, "evidence_links")))))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FederatedParticipant":
        if not isinstance(payload, Mapping):
            raise FederationError("federated participant payload must be a mapping")
        trust_profile = payload.get("trust_profile")
        if not isinstance(trust_profile, TrustProfile):
            trust_profile = TrustProfile.from_mapping(trust_profile or {})
        return cls(
            participant_id=_require_text(payload.get("participant_id") or trust_profile.participant_id, "participant_id"),
            home_network=_require_text(payload.get("home_network"), "home_network"),
            roles=tuple(payload.get("roles", ())),  # type: ignore[arg-type]
            trust_profile=trust_profile,
            federation_status=_require_text(payload.get("federation_status", "pending"), "federation_status"),
            federation_weight=float(payload.get("federation_weight", 0.85)),
            verification_level=_require_text(payload.get("verification_level", "verified"), "verification_level"),
            cross_network_events=int(payload.get("cross_network_events", 0)),
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def local_trust_score(self) -> float:
        return round(self.trust_profile.trust_score, 6)

    @property
    def federated_trust_score(self) -> float:
        return derive_federated_trust(
            self.local_trust_score,
            self.federation_weight,
            self.verification_level,
        )

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and self.federation_status == "verified"
            and self.trust_profile.verified
            and self.federated_trust_score <= self.local_trust_score
            and 0.0 <= self.federated_trust_score <= 100.0
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "cross_network_events": self.cross_network_events,
            "evidence_links": list(self.evidence_links),
            "federated_trust_score": self.federated_trust_score,
            "federation_status": self.federation_status,
            "federation_weight": round(self.federation_weight, 6),
            "home_network": self.home_network,
            "identity_is_reference_only": True,
            "identity_is_truth_authority": False,
            "identity_overrides_payment": False,
            "identity_overrides_proof": False,
            "identity_overrides_replay": False,
            "identity_overrides_runtime_admissibility": False,
            "local_trust_score": self.local_trust_score,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "participant_hash": self.participant_hash,
            "roles": list(self.roles),
            "schema": "afritech.mobility.federated_participant.v1",
            "trust_profile": self.trust_profile.canonical_dict(),
            "verification_level": self.verification_level,
            "verified": self.verified,
        }

    @property
    def participant_hash(self) -> str:
        payload = {
            "authority_boundary": self.authority_boundary,
            "cross_network_events": self.cross_network_events,
            "evidence_links": list(self.evidence_links),
            "federated_trust_score": self.federated_trust_score,
            "federation_status": self.federation_status,
            "federation_weight": round(self.federation_weight, 6),
            "home_network": self.home_network,
            "identity_is_reference_only": True,
            "identity_is_truth_authority": False,
            "identity_overrides_payment": False,
            "identity_overrides_proof": False,
            "identity_overrides_replay": False,
            "identity_overrides_runtime_admissibility": False,
            "local_trust_score": self.local_trust_score,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "roles": list(self.roles),
            "schema": "afritech.mobility.federated_participant.v1",
            "trust_profile": self.trust_profile.canonical_dict(),
            "verification_level": self.verification_level,
            "verified": self.verified,
        }
        return _canonical_hash(payload)

    def to_mobility_participant(
        self,
        *,
        display_name: str,
        verification_status: str = "verified",
        metadata: Mapping[str, Any] | None = None,
    ) -> MobilityParticipant:
        participant = MobilityParticipant(
            participant_id=self.participant_id,
            display_name=_require_text(display_name, "display_name"),
            roles=self.roles,
            verification_status=_require_text(verification_status, "verification_status"),
            trust_score=self.federated_trust_score,
            evidence_links=self.evidence_links + tuple(self.trust_profile.evidence_links),
            metadata=_freeze_mapping(metadata),
        )
        return validate_mobility_participant(participant)

    def to_dispatch_candidate(
        self,
        *,
        location: GeoPoint | Mapping[str, Any],
        reliability_score: float,
        anomaly_rate: float,
        supported_operations: Iterable[object],
        capacity: int = 1,
        availability: bool = True,
        metadata: Mapping[str, Any] | None = None,
        display_name: str | None = None,
    ) -> DispatchCandidate:
        participant = self.to_mobility_participant(
            display_name=display_name or self.participant_id,
            verification_status="verified",
            metadata=metadata,
        )
        return DispatchCandidate.from_mapping(
            {
                "participant": participant.canonical_dict(),
                "location": location,
                "availability": availability,
                "reliability_score": reliability_score,
                "anomaly_rate": anomaly_rate,
                "supported_operations": list(supported_operations),
                "capacity": capacity,
                "metadata": metadata or {},
            }
        )


@dataclass(frozen=True)
class FederationUnit:
    unit_id: str
    network_id: str
    unit_type: str
    members: tuple[str, ...]
    trust_score: float
    certification_status: str
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "unit_id", _require_text(self.unit_id, "unit_id"))
        object.__setattr__(self, "network_id", _require_text(self.network_id, "network_id"))
        if self.unit_type not in ALLOWED_UNIT_TYPES:
            raise FederationError(f"unsupported unit_type: {self.unit_type}")
        members = tuple(_require_text(member, "member") for member in self.members)
        if not members:
            raise FederationError("at least one member is required")
        object.__setattr__(self, "members", tuple(sorted(set(members))))
        object.__setattr__(self, "trust_score", _require_number(self.trust_score, "trust_score", minimum=0.0, maximum=100.0))
        if self.certification_status not in ALLOWED_CERTIFICATION_STATUSES:
            raise FederationError(f"unsupported certification_status: {self.certification_status}")
        object.__setattr__(self, "evidence_links", tuple(sorted(set(_normalize_text_tuple(self.evidence_links, "evidence_links")))))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FederationUnit":
        if not isinstance(payload, Mapping):
            raise FederationError("federation unit payload must be a mapping")
        return cls(
            unit_id=_require_text(payload.get("unit_id") or payload.get("id"), "unit_id"),
            network_id=_require_text(payload.get("network_id"), "network_id"),
            unit_type=_require_text(payload.get("unit_type"), "unit_type"),
            members=tuple(payload.get("members", ())),  # type: ignore[arg-type]
            trust_score=float(payload.get("trust_score", 0.0)),
            certification_status=_require_text(payload.get("certification_status", "pending"), "certification_status"),
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and self.certification_status == "verified" and 0.0 <= self.trust_score <= 100.0

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "certification_status": self.certification_status,
            "evidence_links": list(self.evidence_links),
            "members": list(self.members),
            "metadata": dict(self.metadata),
            "network_id": self.network_id,
            "schema": "afritech.mobility.federation_unit.v1",
            "trust_score": round(self.trust_score, 6),
            "unit_hash": self.unit_hash,
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "verified": self.verified,
        }

    @property
    def unit_hash(self) -> str:
        payload = {
            "authority_boundary": self.authority_boundary,
            "certification_status": self.certification_status,
            "evidence_links": list(self.evidence_links),
            "members": list(self.members),
            "metadata": dict(self.metadata),
            "network_id": self.network_id,
            "schema": "afritech.mobility.federation_unit.v1",
            "trust_score": round(self.trust_score, 6),
            "unit_id": self.unit_id,
            "unit_type": self.unit_type,
            "verified": self.verified,
        }
        return _canonical_hash(payload)


@dataclass(frozen=True)
class FederationState:
    federation_id: str
    participants: tuple[FederatedParticipant, ...] = field(default_factory=tuple)
    units: tuple[FederationUnit, ...] = field(default_factory=tuple)
    transitions: tuple[FederationTransition, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "federation_id", _require_text(self.federation_id, "federation_id"))
        participants = tuple(
            item if isinstance(item, FederatedParticipant) else FederatedParticipant.from_mapping(item)
            for item in self.participants
        )
        units = tuple(
            item if isinstance(item, FederationUnit) else FederationUnit.from_mapping(item)
            for item in self.units
        )
        transitions = tuple(
            item if isinstance(item, FederationTransition) else FederationTransition.from_mapping(item)
            for item in self.transitions
        )
        if not participants:
            raise FederationError("at least one federated participant is required")
        object.__setattr__(self, "participants", participants)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "transitions", transitions)
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FederationState":
        if not isinstance(payload, Mapping):
            raise FederationError("federation state payload must be a mapping")
        return cls(
            federation_id=_require_text(payload.get("federation_id") or payload.get("id"), "federation_id"),
            participants=tuple(payload.get("participants", ())),  # type: ignore[arg-type]
            units=tuple(payload.get("units", ())),  # type: ignore[arg-type]
            transitions=tuple(payload.get("transitions", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def participant_ids(self) -> tuple[str, ...]:
        return tuple(participant.participant_id for participant in self.participants)

    @property
    def network_ids(self) -> tuple[str, ...]:
        return tuple(sorted(set(participant.home_network for participant in self.participants)))

    @property
    def unit_ids(self) -> tuple[str, ...]:
        return tuple(unit.unit_id for unit in self.units)

    @property
    def transition_ids(self) -> tuple[str, ...]:
        return tuple(transition.transition_id for transition in self.transitions)

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.state_hash) == 64
            and len(set(self.participant_ids)) == len(self.participants)
            and all(participant.verified for participant in self.participants)
            and all(unit.verified for unit in self.units)
            and all(transition.verified for transition in self.transitions)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "federation_id": self.federation_id,
            "network_ids": list(self.network_ids),
            "participant_ids": list(self.participant_ids),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "schema": SCHEMA,
            "state_hash": self.state_hash,
            "transition_count": len(self.transitions),
            "transitions": [transition.canonical_dict() for transition in self.transitions],
            "unit_ids": list(self.unit_ids),
            "units": [unit.canonical_dict() for unit in self.units],
            "verified": self.verified,
        }

    @property
    def state_hash(self) -> str:
        payload = {
            "authority_boundary": self.authority_boundary,
            "federation_id": self.federation_id,
            "network_ids": list(self.network_ids),
            "participant_ids": list(self.participant_ids),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "schema": SCHEMA,
            "transitions": [transition.canonical_dict() for transition in self.transitions],
            "unit_ids": list(self.unit_ids),
            "units": [unit.canonical_dict() for unit in self.units],
        }
        return _canonical_hash(payload)

    def dispatch_candidates(
        self,
        *,
        location: GeoPoint | Mapping[str, Any],
        reliability_score: float,
        anomaly_rate: float,
        supported_operations: Iterable[object],
        capacity: int = 1,
        availability: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> tuple[DispatchCandidate, ...]:
        return tuple(
            participant.to_dispatch_candidate(
                location=location,
                reliability_score=reliability_score,
                anomaly_rate=anomaly_rate,
                supported_operations=supported_operations,
                capacity=capacity,
                availability=availability,
                metadata=metadata,
                display_name=participant.participant_id,
            )
            for participant in self.participants
        )


@dataclass(frozen=True)
class FederationInvariantCheck:
    identifier: str
    satisfied: bool
    details: str
    evidence_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "details": self.details,
            "evidence_hash": self.evidence_hash,
            "identifier": self.identifier,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class FederationInvariantReport:
    federation_hash: str
    check_hash: str
    proof_hash: str
    checks: tuple[FederationInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "federation_hash": self.federation_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.federation_invariant_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class FederationValidationReport:
    federation_hash: str
    invariant_report_hash: str
    proof_hash: str
    verified: bool
    authority_boundary: str = AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "federation_hash": self.federation_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.federation_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def build_federation_state(
    federation_id: str,
    participants: Iterable[FederatedParticipant | Mapping[str, Any]],
    *,
    units: Iterable[FederationUnit | Mapping[str, Any]] = (),
    transitions: Iterable[FederationTransition | Mapping[str, Any]] = (),
) -> FederationState:
    return FederationState(
        federation_id=_require_text(federation_id, "federation_id"),
        participants=tuple(participants),
        units=tuple(units),
        transitions=tuple(transitions),
    )


def evaluate_federation_invariants(
    state: FederationState | Mapping[str, Any],
) -> FederationInvariantReport:
    normalized = state if isinstance(state, FederationState) else FederationState.from_mapping(state)
    replay = build_federation_state(
        normalized.federation_id,
        normalized.participants,
        units=normalized.units,
        transitions=normalized.transitions,
    )
    checks = (
        _check_membership_verifiable(normalized),
        _check_trust_transfer_bounded(normalized),
        _check_replayable(normalized, replay),
        _check_no_authority(normalized),
        _check_unique_identity(normalized),
        _check_hash_stable(normalized),
    )
    proof = _federation_proof_payload(
        normalized,
        verified=normalized.verified and all(check.satisfied for check in checks),
    )
    return FederationInvariantReport(
        federation_hash=normalized.state_hash,
        check_hash=_hash_checks(checks),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_federation_state(state: FederationState | Mapping[str, Any]) -> FederationValidationReport:
    supplied_hash = state.get("state_hash") if isinstance(state, Mapping) else None
    normalized = state if isinstance(state, FederationState) else FederationState.from_mapping(state)
    invariant_report = evaluate_federation_invariants(normalized)
    validate_federation_invariants(invariant_report)
    replay = build_federation_state(
        normalized.federation_id,
        normalized.participants,
        units=normalized.units,
        transitions=normalized.transitions,
    )
    if normalized.canonical_dict() != replay.canonical_dict():
        raise FederationError("federation state does not replay deterministically")
    if supplied_hash is not None and _require_hash(supplied_hash, "state_hash") != normalized.state_hash:
        raise FederationError("supplied federation state hash mismatch")
    proof = _federation_proof_payload(normalized, verified=normalized.verified and invariant_report.verified)
    report = FederationValidationReport(
        federation_hash=normalized.state_hash,
        invariant_report_hash=invariant_report.report_hash(),
        proof_hash=proof["proof_hash"],
        verified=proof["verified"],
    )
    if not report.verified:
        raise FederationError("federation state failed validation")
    return report


def _federation_proof_payload(state: FederationState, *, verified: bool) -> dict[str, Any]:
    proof = {
        "schema": "afritech.mobility.federation_proof.v1",
        "authority_boundary": "federation_proof_read_only",
        "federation_id": state.federation_id,
        "state_hash": state.state_hash,
        "participant_ids": list(state.participant_ids),
        "unit_ids": list(state.unit_ids),
        "network_ids": list(state.network_ids),
        "transition_count": len(state.transitions),
        "trust_transfer_count": len(state.transitions),
        "verified": verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def validate_federation_invariants(report: FederationInvariantReport) -> bool:
    if not isinstance(report, FederationInvariantReport):
        raise FederationError("report must be a FederationInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise FederationError("federation invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise FederationError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise FederationError(f"{check.identifier} failed: {check.details}")
    return True


def build_federation_proof(state: FederationState | Mapping[str, Any]) -> dict[str, Any]:
    normalized = state if isinstance(state, FederationState) else FederationState.from_mapping(state)
    report = validate_federation_state(normalized)
    return _federation_proof_payload(normalized, verified=report.verified)


def export_federation_proof(
    state: FederationState | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    normalized = state if isinstance(state, FederationState) else FederationState.from_mapping(state)
    proof = build_federation_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "federation_state.json"
    proof_path = target / "federation_proof.json"
    json_path.write_text(
        json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    proof_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path, "proof": proof_path}


INVARIANT_IDS = (
    "IA-FEDERATION-001",
    "IA-FEDERATION-002",
    "IA-FEDERATION-003",
    "IA-FEDERATION-004",
    "IA-FEDERATION-005",
    "IA-FEDERATION-006",
)


def _check_membership_verifiable(state: FederationState) -> FederationInvariantCheck:
    participant_ids = list(state.participant_ids)
    unit_members = [member for unit in state.units for member in unit.members]
    all_members_known = all(member in participant_ids for member in unit_members)
    participants_verified = all(
        participant.verified
        and participant.trust_profile.verified
        and participant.federation_status == "verified"
        for participant in state.participants
    )
    units_verified = all(unit.verified for unit in state.units)
    transitions_verified = all(transition.verified for transition in state.transitions)
    satisfied = all((all_members_known, participants_verified, units_verified, transitions_verified))
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-001",
        satisfied=satisfied,
        details="federation membership is verifiable",
        evidence_hash=state.state_hash,
    )


def _check_trust_transfer_bounded(state: FederationState) -> FederationInvariantCheck:
    satisfied = True
    for participant in state.participants:
        if participant.federated_trust_score > participant.local_trust_score:
            satisfied = False
        if not 0.0 <= participant.federated_trust_score <= 100.0:
            satisfied = False
    for transition in state.transitions:
        if not 0.0 <= transition.trust_transferred <= 100.0:
            satisfied = False
        participant = next((item for item in state.participants if item.participant_id == transition.participant_id), None)
        if participant is not None and transition.trust_transferred > participant.local_trust_score:
            satisfied = False
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-002",
        satisfied=satisfied,
        details="trust transfer is bounded",
        evidence_hash=state.state_hash,
    )


def _check_replayable(state: FederationState, replay: FederationState) -> FederationInvariantCheck:
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-003",
        satisfied=state.canonical_dict() == replay.canonical_dict(),
        details="cross-network operations are replayable",
        evidence_hash=state.state_hash,
    )


def _check_no_authority(state: FederationState) -> FederationInvariantCheck:
    payload = state.canonical_dict()
    satisfied = (
        payload["authority_boundary"] == AUTHORITY_BOUNDARY
        and payload["verified"] is True
        and all(participant.canonical_dict()["identity_is_reference_only"] is True for participant in state.participants)
    )
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-004",
        satisfied=satisfied,
        details="federation cannot introduce authority over proof",
        evidence_hash=state.state_hash,
    )


def _check_unique_identity(state: FederationState) -> FederationInvariantCheck:
    participant_ids = list(state.participant_ids)
    satisfied = len(participant_ids) == len(set(participant_ids))
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-005",
        satisfied=satisfied,
        details="participant identity remains unique across networks",
        evidence_hash=state.state_hash,
    )


def _check_hash_stable(state: FederationState) -> FederationInvariantCheck:
    satisfied = len(state.state_hash) == 64 and FederationState.from_mapping(state.canonical_dict()).state_hash == state.state_hash
    return FederationInvariantCheck(
        identifier="IA-FEDERATION-006",
        satisfied=satisfied,
        details="federation data hash is stable",
        evidence_hash=state.state_hash,
    )


def _hash_checks(checks: tuple[FederationInvariantCheck, ...]) -> str:
    return _canonical_hash([check.canonical_dict() for check in checks])


__all__ = [
    "ALLOWED_CERTIFICATION_STATUSES",
    "ALLOWED_FEDERATION_STATUSES",
    "ALLOWED_UNIT_TYPES",
    "ALLOWED_VERIFICATION_LEVELS",
    "AUTHORITY_BOUNDARY",
    "FederatedParticipant",
    "FederationError",
    "FederationInvariantCheck",
    "FederationInvariantReport",
    "FederationState",
    "FederationTransition",
    "FederationUnit",
    "FederationValidationReport",
    "INVARIANT_IDS",
    "SCHEMA",
    "VERIFICATION_FACTORS",
    "build_federation_proof",
    "build_federation_state",
    "derive_federated_trust",
    "evaluate_federation_invariants",
    "export_federation_proof",
    "validate_federation_invariants",
    "validate_federation_state",
]
