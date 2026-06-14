"""Deterministic federated trust network for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant, validate_mobility_participant


SCHEMA = "afritech.mobility.trust_profile.v1"
AUTHORITY_BOUNDARY = "trust_network_reference_only"

ALLOWED_EVENT_TYPES = (
    "successful_delivery",
    "successful_pickup",
    "settlement_completed",
    "delay_reported",
    "custody_gap",
    "dispute_opened",
    "dispute_resolved",
    "anomaly_detected",
    "evidence_forgery",
    "timestamp_skew",
    "replay_attack",
    "provider_callback_forgery",
)

SUCCESS_EVENT_TYPES = {
    "successful_delivery",
    "successful_pickup",
    "settlement_completed",
    "dispute_resolved",
}

ANOMALY_EVENT_TYPES = {
    "delay_reported",
    "custody_gap",
    "anomaly_detected",
    "evidence_forgery",
    "timestamp_skew",
    "replay_attack",
    "provider_callback_forgery",
}

DISPUTE_EVENT_TYPES = {"dispute_opened", "dispute_resolved"}

EVENT_SIGNALS = {
    "successful_delivery": 8.0,
    "successful_pickup": 7.0,
    "settlement_completed": 5.5,
    "delay_reported": -4.5,
    "custody_gap": -16.0,
    "dispute_opened": -10.0,
    "dispute_resolved": 2.5,
    "anomaly_detected": -12.0,
    "evidence_forgery": -25.0,
    "timestamp_skew": -8.0,
    "replay_attack": -20.0,
    "provider_callback_forgery": -22.0,
}

DEFAULT_EVENT_RATINGS = {
    "successful_delivery": 5.0,
    "successful_pickup": 5.0,
    "settlement_completed": 4.5,
    "delay_reported": 2.0,
    "custody_gap": 1.0,
    "dispute_opened": 1.5,
    "dispute_resolved": 3.5,
    "anomaly_detected": 1.0,
    "evidence_forgery": 0.5,
    "timestamp_skew": 1.5,
    "replay_attack": 0.5,
    "provider_callback_forgery": 0.5,
}


class TrustNetworkError(ValueError):
    """Raised when a trust network payload or report is invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrustNetworkError(f"{label} is required")
    return value.strip()


def _require_hash(value: object, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64:
        raise TrustNetworkError(f"{label} must be a 64-character hex digest")
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TrustNetworkError(f"{label} must be boolean")
    return value


def _require_number(
    value: object,
    label: str,
    *,
    minimum: float,
    maximum: float,
    precision: int = 6,
) -> float:
    if not isinstance(value, (int, float)):
        raise TrustNetworkError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise TrustNetworkError(f"{label} must be between {minimum} and {maximum}")
    return round(number, precision)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise TrustNetworkError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _normalize_links(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TrustNetworkError("evidence_links must be iterable")
    normalized = tuple(_require_text(value, "evidence_link") for value in values)
    return tuple(sorted(set(normalized)))


def _normalize_event_history(values: Iterable[object]) -> tuple["TrustUpdateEvent", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TrustNetworkError("event_history must be iterable")
    events: list[TrustUpdateEvent] = []
    for item in values:
        if isinstance(item, TrustUpdateEvent):
            events.append(item)
        elif isinstance(item, Mapping):
            events.append(TrustUpdateEvent.from_mapping(item))
        else:
            raise TrustNetworkError("event_history must contain mappings or TrustUpdateEvent objects")
    return tuple(events)


def _event_signal(event_type: str) -> float:
    return EVENT_SIGNALS[event_type]


def _event_rating(event_type: str, rating: float | None) -> float:
    if rating is None:
        rating = DEFAULT_EVENT_RATINGS[event_type]
    return _require_number(rating, "rating", minimum=0.0, maximum=5.0)


def _score_event_sequence(events: tuple["TrustUpdateEvent", ...]) -> float:
    score = 50.0
    total = max(1, len(events))
    for index, event in enumerate(events):
        recency_weight = 1.0 + (index / max(1, total - 1)) * 0.25
        rating_bonus = (event.rating - 3.0) * 1.8
        score = score * 0.93 + (_event_signal(event.event_type) * recency_weight) + rating_bonus
        score = max(0.0, min(100.0, round(score, 6)))
    return score


def _summarize_events(events: tuple["TrustUpdateEvent", ...]) -> dict[str, Any]:
    total = len(events)
    successful = sum(1 for event in events if event.event_type in SUCCESS_EVENT_TYPES)
    anomalies = sum(1 for event in events if event.event_type in ANOMALY_EVENT_TYPES)
    disputes = sum(1 for event in events if event.event_type in DISPUTE_EVENT_TYPES)
    average_rating = round(
        sum(event.rating for event in events) / total if total else 3.0,
        6,
    )
    evidence_links = tuple(
        sorted({event.evidence_link for event in events if event.evidence_link})
    )
    last_updated = str(max((event.timestamp for event in events), default=0))
    trust_score = _score_event_sequence(events)
    return {
        "average_rating": average_rating,
        "anomaly_events": anomalies,
        "disputes": disputes,
        "evidence_links": evidence_links,
        "last_updated": last_updated,
        "successful_operations": successful,
        "total_operations": total,
        "trust_score": trust_score,
    }


@dataclass(frozen=True)
class TrustUpdateEvent:
    event_id: str
    participant_id: str
    event_type: str
    source_operation_id: str
    dispatch_hash: str
    custody_hash: str
    settlement_hash: str
    evidence_link: str
    timestamp: int
    rating: float | None = None
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise TrustNetworkError(f"unsupported event_type: {self.event_type}")
        object.__setattr__(self, "source_operation_id", _require_text(self.source_operation_id, "source_operation_id"))
        object.__setattr__(self, "dispatch_hash", _require_hash(self.dispatch_hash, "dispatch_hash"))
        object.__setattr__(self, "custody_hash", _require_hash(self.custody_hash, "custody_hash"))
        object.__setattr__(self, "settlement_hash", _require_hash(self.settlement_hash, "settlement_hash"))
        object.__setattr__(self, "evidence_link", _require_text(self.evidence_link, "evidence_link"))
        if not isinstance(self.timestamp, int):
            raise TrustNetworkError("timestamp must be an integer")
        object.__setattr__(self, "rating", _event_rating(self.event_type, self.rating))
        object.__setattr__(self, "verified", _require_bool(self.verified, "verified"))
        if not self.verified:
            raise TrustNetworkError("trust update events must derive from verified operations")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TrustUpdateEvent":
        if not isinstance(payload, Mapping):
            raise TrustNetworkError("trust update payload must be a mapping")
        return cls(
            event_id=_require_text(payload.get("event_id") or payload.get("id"), "event_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            event_type=_require_text(payload.get("event_type"), "event_type"),
            source_operation_id=_require_text(payload.get("source_operation_id"), "source_operation_id"),
            dispatch_hash=_require_text(payload.get("dispatch_hash") or payload.get("dispatch"), "dispatch_hash"),
            custody_hash=_require_text(payload.get("custody_hash") or payload.get("custody"), "custody_hash"),
            settlement_hash=_require_text(payload.get("settlement_hash") or payload.get("settlement"), "settlement_hash"),
            evidence_link=_require_text(payload.get("evidence_link") or payload.get("evidence"), "evidence_link"),
            timestamp=int(payload.get("timestamp", 0)),
            rating=payload.get("rating"),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "custody_hash": self.custody_hash,
            "dispatch_hash": self.dispatch_hash,
            "evidence_link": self.evidence_link,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "rating": self.rating,
            "settlement_hash": self.settlement_hash,
            "source_operation_id": self.source_operation_id,
            "timestamp": self.timestamp,
            "verified": self.verified,
            "event_hash": self.event_hash,
        }

    @property
    def event_hash(self) -> str:
        payload = {
            "custody_hash": self.custody_hash,
            "dispatch_hash": self.dispatch_hash,
            "evidence_link": self.evidence_link,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "rating": self.rating,
            "settlement_hash": self.settlement_hash,
            "source_operation_id": self.source_operation_id,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }
        return _canonical_hash(payload)


@dataclass(frozen=True)
class TrustProfile:
    participant_id: str
    total_operations: int
    successful_operations: int
    anomaly_events: int
    disputes: int
    average_rating: float
    trust_score: float
    last_updated: str
    event_history: tuple[TrustUpdateEvent, ...] = field(default_factory=tuple)
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        if not isinstance(self.total_operations, int) or self.total_operations < 0:
            raise TrustNetworkError("total_operations must be a non-negative integer")
        if not isinstance(self.successful_operations, int) or self.successful_operations < 0:
            raise TrustNetworkError("successful_operations must be a non-negative integer")
        if not isinstance(self.anomaly_events, int) or self.anomaly_events < 0:
            raise TrustNetworkError("anomaly_events must be a non-negative integer")
        if not isinstance(self.disputes, int) or self.disputes < 0:
            raise TrustNetworkError("disputes must be a non-negative integer")
        object.__setattr__(self, "average_rating", _require_number(self.average_rating, "average_rating", minimum=0.0, maximum=5.0))
        object.__setattr__(self, "trust_score", _require_number(self.trust_score, "trust_score", minimum=0.0, maximum=100.0))
        object.__setattr__(self, "last_updated", _require_text(self.last_updated, "last_updated"))
        object.__setattr__(self, "event_history", _normalize_event_history(self.event_history))
        object.__setattr__(self, "evidence_links", _normalize_links(self.evidence_links))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TrustProfile":
        if not isinstance(payload, Mapping):
            raise TrustNetworkError("trust profile payload must be a mapping")
        return cls(
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            total_operations=int(payload.get("total_operations", 0)),
            successful_operations=int(payload.get("successful_operations", 0)),
            anomaly_events=int(payload.get("anomaly_events", 0)),
            disputes=int(payload.get("disputes", 0)),
            average_rating=float(payload.get("average_rating", 3.0)),
            trust_score=float(payload.get("trust_score", 50.0)),
            last_updated=_require_text(payload.get("last_updated") or "0", "last_updated"),
            event_history=tuple(payload.get("event_history", ())),  # type: ignore[arg-type]
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.profile_hash) == 64
            and 0.0 <= self.trust_score <= 100.0
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "anomaly_events": self.anomaly_events,
            "authority_boundary": self.authority_boundary,
            "average_rating": round(self.average_rating, 6),
            "disputes": self.disputes,
            "evidence_links": list(self.evidence_links),
            "event_history": [event.canonical_dict() for event in self.event_history],
            "identity_is_reference_only": True,
            "identity_is_truth_authority": False,
            "identity_overrides_payment": False,
            "identity_overrides_proof": False,
            "identity_overrides_replay": False,
            "identity_overrides_runtime_admissibility": False,
            "last_updated": self.last_updated,
            "participant_id": self.participant_id,
            "profile_hash": self.profile_hash,
            "schema": SCHEMA,
            "successful_operations": self.successful_operations,
            "total_operations": self.total_operations,
            "trust_score": round(self.trust_score, 6),
            "verified": self.verified,
        }

    @property
    def profile_hash(self) -> str:
        payload = {
            "anomaly_events": self.anomaly_events,
            "authority_boundary": self.authority_boundary,
            "average_rating": round(self.average_rating, 6),
            "disputes": self.disputes,
            "evidence_links": list(self.evidence_links),
            "event_history": [event.canonical_dict() for event in self.event_history],
            "identity_is_reference_only": True,
            "identity_is_truth_authority": False,
            "identity_overrides_payment": False,
            "identity_overrides_proof": False,
            "identity_overrides_replay": False,
            "identity_overrides_runtime_admissibility": False,
            "last_updated": self.last_updated,
            "participant_id": self.participant_id,
            "schema": SCHEMA,
            "successful_operations": self.successful_operations,
            "total_operations": self.total_operations,
            "trust_score": round(self.trust_score, 6),
        }
        return _canonical_hash(payload)

    def to_mobility_participant(
        self,
        *,
        display_name: str,
        roles: Iterable[object],
        verification_status: str = "verified",
        metadata: Mapping[str, Any] | None = None,
    ) -> MobilityParticipant:
        participant = MobilityParticipant(
            participant_id=self.participant_id,
            display_name=_require_text(display_name, "display_name"),
            roles=tuple(roles),  # type: ignore[arg-type]
            verification_status=_require_text(verification_status, "verification_status"),
            trust_score=self.trust_score,
            evidence_links=self.evidence_links,
            metadata=_freeze_mapping(metadata),
        )
        return validate_mobility_participant(participant)


@dataclass(frozen=True)
class TrustInvariantCheck:
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
class TrustInvariantReport:
    profile_hash: str
    check_hash: str
    checks: tuple[TrustInvariantCheck, ...]
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "profile_hash": self.profile_hash,
            "schema": "afritech.mobility.trust_invariant_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class TrustValidationReport:
    profile_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "invariant_report_hash": self.invariant_report_hash,
            "profile_hash": self.profile_hash,
            "schema": "afritech.mobility.trust_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def build_trust_profile(
    participant_id: str,
    event_history: Iterable[TrustUpdateEvent | Mapping[str, Any]] = (),
    *,
    evidence_links: Iterable[object] = (),
) -> TrustProfile:
    normalized_events = _normalize_event_history(event_history)
    summary = _summarize_events(normalized_events)
    extra_links = _normalize_links(evidence_links)
    combined_links = tuple(sorted(set(summary["evidence_links"]) | set(extra_links)))
    return TrustProfile(
        participant_id=_require_text(participant_id, "participant_id"),
        total_operations=summary["total_operations"],
        successful_operations=summary["successful_operations"],
        anomaly_events=summary["anomaly_events"],
        disputes=summary["disputes"],
        average_rating=summary["average_rating"],
        trust_score=summary["trust_score"],
        last_updated=summary["last_updated"],
        event_history=normalized_events,
        evidence_links=combined_links,
    )


def update_trust_profile(
    profile: TrustProfile | Mapping[str, Any],
    event: TrustUpdateEvent | Mapping[str, Any],
) -> TrustProfile:
    normalized_profile = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    normalized_event = event if isinstance(event, TrustUpdateEvent) else TrustUpdateEvent.from_mapping(event)
    if normalized_profile.participant_id != normalized_event.participant_id:
        raise TrustNetworkError("trust event participant does not match profile participant")
    return build_trust_profile(
        normalized_profile.participant_id,
        normalized_profile.event_history + (normalized_event,),
        evidence_links=normalized_profile.evidence_links + (normalized_event.evidence_link,),
    )


def evaluate_trust_invariants(profile: TrustProfile | Mapping[str, Any]) -> TrustInvariantReport:
    normalized = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    replay = build_trust_profile(normalized.participant_id, normalized.event_history, evidence_links=normalized.evidence_links)
    checks = (
        _check_same_sequence_same_score(normalized, replay),
        _check_verified_sources_only(normalized),
        _check_replayable(normalized, replay),
        _check_tamper_sensitivity(normalized),
        _check_bounds(normalized),
        _check_no_authority(normalized),
    )
    return TrustInvariantReport(
        profile_hash=normalized.profile_hash,
        check_hash=_hash_checks(checks),
        checks=checks,
    )


def validate_trust_invariants(report: TrustInvariantReport) -> bool:
    if not isinstance(report, TrustInvariantReport):
        raise TrustNetworkError("report must be a TrustInvariantReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise TrustNetworkError("trust invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise TrustNetworkError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise TrustNetworkError(f"{check.identifier} failed: {check.details}")
    return True


def validate_trust_profile(profile: TrustProfile | Mapping[str, Any]) -> TrustValidationReport:
    supplied_hash = None
    if isinstance(profile, Mapping):
        supplied_hash = profile.get("profile_hash")
    normalized = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    replay = build_trust_profile(normalized.participant_id, normalized.event_history, evidence_links=normalized.evidence_links)
    invariant_report = evaluate_trust_invariants(normalized)
    validate_trust_invariants(invariant_report)
    if normalized.canonical_dict() != replay.canonical_dict():
        raise TrustNetworkError("trust profile does not replay deterministically")
    if normalized.profile_hash != replay.profile_hash:
        raise TrustNetworkError("trust profile hash mismatch")
    if supplied_hash is not None and _require_hash(supplied_hash, "profile_hash") != normalized.profile_hash:
        raise TrustNetworkError("supplied trust profile hash mismatch")
    verified = normalized.verified and replay.verified and normalized.trust_score == replay.trust_score
    report = TrustValidationReport(
        profile_hash=normalized.profile_hash,
        invariant_report_hash=invariant_report.report_hash(),
        verified=verified,
    )
    if not report.verified:
        raise TrustNetworkError("trust profile failed validation")
    return report


def build_trust_profile_proof(profile: TrustProfile | Mapping[str, Any]) -> dict[str, Any]:
    normalized = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    report = validate_trust_profile(normalized)
    proof = {
        "schema": "afritech.mobility.trust_profile_proof.v1",
        "authority_boundary": "trust_profile_proof_read_only",
        "participant_id": normalized.participant_id,
        "profile_hash": normalized.profile_hash,
        "event_count": normalized.total_operations,
        "event_history_hash": _canonical_hash([event.canonical_dict() for event in normalized.event_history]),
        "trust_score": round(normalized.trust_score, 6),
        "evidence_links": list(normalized.evidence_links),
        "validation_report_hash": report.report_hash(),
        "verified": report.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def export_trust_profile_proof(
    profile: TrustProfile | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    normalized = profile if isinstance(profile, TrustProfile) else TrustProfile.from_mapping(profile)
    proof = build_trust_profile_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "trust_profile.json"
    proof_path = target / "trust_profile_proof.json"
    json_path.write_text(
        json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    proof_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path, "proof": proof_path}


def _check_same_sequence_same_score(profile: TrustProfile, replay: TrustProfile) -> TrustInvariantCheck:
    satisfied = profile.trust_score == replay.trust_score
    return TrustInvariantCheck(
        identifier="IA-TRUST-001",
        satisfied=satisfied,
        details="same verified event sequence produces the same trust score",
        evidence_hash=profile.profile_hash,
    )


def _check_verified_sources_only(profile: TrustProfile) -> TrustInvariantCheck:
    satisfied = all(
        event.verified
        and len(event.dispatch_hash) == 64
        and len(event.custody_hash) == 64
        and len(event.settlement_hash) == 64
        for event in profile.event_history
    )
    return TrustInvariantCheck(
        identifier="IA-TRUST-002",
        satisfied=satisfied,
        details="trust derives only from verified operations",
        evidence_hash=profile.profile_hash,
    )


def _check_replayable(profile: TrustProfile, replay: TrustProfile) -> TrustInvariantCheck:
    satisfied = profile.canonical_dict() == replay.canonical_dict()
    return TrustInvariantCheck(
        identifier="IA-TRUST-003",
        satisfied=satisfied,
        details="trust evolution is replayable",
        evidence_hash=replay.profile_hash,
    )


def _check_tamper_sensitivity(profile: TrustProfile) -> TrustInvariantCheck:
    if not profile.event_history:
        satisfied = True
    else:
        tampered_event = profile.event_history[0]
        tampered = TrustUpdateEvent(
            event_id=tampered_event.event_id,
            participant_id=tampered_event.participant_id,
            event_type="successful_delivery" if tampered_event.event_type != "successful_delivery" else "delay_reported",
            source_operation_id=tampered_event.source_operation_id,
            dispatch_hash=tampered_event.dispatch_hash,
            custody_hash=tampered_event.custody_hash,
            settlement_hash=tampered_event.settlement_hash,
            evidence_link=tampered_event.evidence_link,
            timestamp=tampered_event.timestamp,
            rating=tampered_event.rating,
            verified=True,
            metadata=tampered_event.metadata,
        )
        tampered_profile = build_trust_profile(
            profile.participant_id,
            (tampered,) + profile.event_history[1:],
            evidence_links=profile.evidence_links,
        )
        satisfied = tampered_profile.profile_hash != profile.profile_hash or tampered_profile.trust_score != profile.trust_score
    return TrustInvariantCheck(
        identifier="IA-TRUST-004",
        satisfied=satisfied,
        details="tampering with event history changes trust state",
        evidence_hash=profile.profile_hash,
    )


def _check_bounds(profile: TrustProfile) -> TrustInvariantCheck:
    satisfied = 0.0 <= profile.trust_score <= 100.0
    return TrustInvariantCheck(
        identifier="IA-TRUST-005",
        satisfied=satisfied,
        details="trust stays within defined bounds",
        evidence_hash=profile.profile_hash,
    )


def _check_no_authority(profile: TrustProfile) -> TrustInvariantCheck:
    payload = profile.canonical_dict()
    satisfied = (
        payload["identity_is_reference_only"] is True
        and payload["identity_is_truth_authority"] is False
        and payload["identity_overrides_payment"] is False
        and payload["identity_overrides_proof"] is False
        and payload["identity_overrides_replay"] is False
        and payload["identity_overrides_runtime_admissibility"] is False
        and profile.authority_boundary == AUTHORITY_BOUNDARY
    )
    return TrustInvariantCheck(
        identifier="IA-TRUST-006",
        satisfied=satisfied,
        details="trust does not introduce a new authority surface",
        evidence_hash=profile.profile_hash,
    )


def _hash_checks(checks: tuple[TrustInvariantCheck, ...]) -> str:
    return _canonical_hash([check.canonical_dict() for check in checks])


INVARIANT_IDS = (
    "IA-TRUST-001",
    "IA-TRUST-002",
    "IA-TRUST-003",
    "IA-TRUST-004",
    "IA-TRUST-005",
    "IA-TRUST-006",
)


__all__ = [
    "ALLOWED_EVENT_TYPES",
    "ANOMALY_EVENT_TYPES",
    "AUTHORITY_BOUNDARY",
    "DISPUTE_EVENT_TYPES",
    "EVENT_SIGNALS",
    "INVARIANT_IDS",
    "SCHEMA",
    "SUCCESS_EVENT_TYPES",
    "TrustInvariantCheck",
    "TrustInvariantReport",
    "TrustNetworkError",
    "TrustProfile",
    "TrustUpdateEvent",
    "TrustValidationReport",
    "build_trust_profile",
    "build_trust_profile_proof",
    "evaluate_trust_invariants",
    "export_trust_profile_proof",
    "update_trust_profile",
    "validate_trust_invariants",
    "validate_trust_profile",
]
