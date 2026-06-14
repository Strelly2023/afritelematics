"""Deterministic trust-aware dispatch engine for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ecosystems.afriride.geo.types import GeoPoint

from afritech.identity.mobility_participant import (
    MobilityParticipant,
    MobilityParticipantError,
    validate_mobility_participant,
)


SCHEMA = "afritech.mobility.trust_dispatch.v1"
AUTHORITY_BOUNDARY = "dispatch_selection_reference_only"


class DispatchRequestError(ValueError):
    """Raised when a dispatch request is invalid."""


class DispatchCandidateError(ValueError):
    """Raised when a dispatch candidate is invalid."""


class DispatchDecisionError(RuntimeError):
    """Raised when a dispatch decision is invalid or non-deterministic."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DispatchRequestError(f"{label} is required")
    return value.strip()


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 100.0) -> float:
    if not isinstance(value, (int, float)):
        raise DispatchCandidateError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise DispatchCandidateError(f"{label} must be between {minimum} and {maximum}")
    return round(number, 6)


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise DispatchRequestError("mapping expected")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _geo_from_value(value: GeoPoint | Mapping[str, Any]) -> GeoPoint:
    if isinstance(value, GeoPoint):
        return value
    if not isinstance(value, Mapping):
        raise DispatchRequestError("geo point must be a mapping or GeoPoint")
    try:
        return GeoPoint(
            lat=float(value["lat"]),
            lon=float(value["lon"]),
            timestamp=int(value["timestamp"]),
        )
    except KeyError as exc:  # pragma: no cover - defensive
        raise DispatchRequestError(f"missing geo field: {exc.args[0]}") from exc


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, round(value, 6)))


def _haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    from math import asin, cos, radians, sin, sqrt

    lat1 = radians(a.lat)
    lat2 = radians(b.lat)
    dlat = lat2 - lat1
    dlon = radians(b.lon - a.lon)
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(hav))


def _normalize_roles(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise DispatchCandidateError("required_roles must be iterable")
    normalized = tuple(_require_text(value, "required_role") for value in values)
    if any(not value for value in normalized):
        raise DispatchCandidateError("required_roles cannot contain empty values")
    return tuple(sorted(set(normalized)))


def _normalize_operations(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise DispatchCandidateError("required_operations must be iterable")
    normalized = tuple(_require_text(value, "required_operation") for value in values)
    if any(not value for value in normalized):
        raise DispatchCandidateError("required_operations cannot contain empty values")
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class DispatchRequest:
    operation_id: str
    operation_type: str
    origin: GeoPoint
    destination: GeoPoint
    constraints: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    timestamp: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        object.__setattr__(self, "operation_type", _require_text(self.operation_type, "operation_type"))
        object.__setattr__(self, "origin", _geo_from_value(self.origin))
        object.__setattr__(self, "destination", _geo_from_value(self.destination))
        if not isinstance(self.timestamp, int):
            raise DispatchRequestError("timestamp must be an integer")
        object.__setattr__(self, "constraints", _freeze_mapping(dict(self.constraints)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DispatchRequest":
        if not isinstance(payload, Mapping):
            raise DispatchRequestError("request payload must be a mapping")
        return cls(
            operation_id=_require_text(payload.get("operation_id") or payload.get("id"), "operation_id"),
            operation_type=_require_text(payload.get("operation_type"), "operation_type"),
            origin=_geo_from_value(payload.get("origin", {})),
            destination=_geo_from_value(payload.get("destination", {})),
            constraints=_freeze_mapping(payload.get("constraints", {})),
            timestamp=int(payload.get("timestamp", 0)),
        )

    @property
    def constraint_map(self) -> dict[str, Any]:
        return dict(self.constraints)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": AUTHORITY_BOUNDARY,
            "constraints": self.constraint_map,
            "destination": self.destination.canonical(),
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "origin": self.origin.canonical(),
            "schema": SCHEMA,
            "timestamp": self.timestamp,
        }

    def request_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class DispatchCandidate:
    participant: MobilityParticipant
    location: GeoPoint
    availability: bool = True
    reliability_score: float = 0.0
    anomaly_rate: float = 0.0
    supported_operations: tuple[str, ...] = field(default_factory=tuple)
    capacity: int = 1
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        participant = validate_mobility_participant(self.participant)
        object.__setattr__(self, "participant", participant)
        object.__setattr__(self, "location", _geo_from_value(self.location))
        object.__setattr__(self, "reliability_score", _require_number(self.reliability_score, "reliability_score"))
        object.__setattr__(self, "anomaly_rate", _require_number(self.anomaly_rate, "anomaly_rate"))
        if not isinstance(self.availability, bool):
            raise DispatchCandidateError("availability must be boolean")
        if not isinstance(self.capacity, int) or self.capacity < 1:
            raise DispatchCandidateError("capacity must be a positive integer")
        object.__setattr__(self, "supported_operations", _normalize_operations(self.supported_operations))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DispatchCandidate":
        if not isinstance(payload, Mapping):
            raise DispatchCandidateError("candidate payload must be a mapping")
        participant = payload.get("participant")
        if participant is None:
            raise DispatchCandidateError("candidate participant is required")
        return cls(
            participant=validate_mobility_participant(participant),
            location=_geo_from_value(payload.get("location", {})),
            availability=bool(payload.get("availability", True)),
            reliability_score=float(payload.get("reliability_score", 0.0)),
            anomaly_rate=float(payload.get("anomaly_rate", 0.0)),
            supported_operations=tuple(payload.get("supported_operations", ())),  # type: ignore[arg-type]
            capacity=int(payload.get("capacity", 1)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    @property
    def candidate_id(self) -> str:
        return self.participant.participant_id

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "availability": self.availability,
            "candidate_id": self.candidate_id,
            "capacity": self.capacity,
            "location": self.location.canonical(),
            "metadata": dict(self.metadata),
            "participant": self.participant.canonical_dict(),
            "reliability_score": self.reliability_score,
            "supported_operations": self.supported_operations,
            "anomaly_rate": self.anomaly_rate,
        }

    def candidate_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class DispatchRankedCandidate:
    participant_id: str
    candidate_hash: str
    score: float
    trust_score: float
    reliability_score: float
    route_efficiency: float
    constraint_match: float
    anomaly_rate: float
    eligible: bool
    explanation: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DispatchRankedCandidate":
        if not isinstance(payload, Mapping):
            raise DispatchDecisionError("ranked candidate payload must be a mapping")
        return cls(
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            candidate_hash=_require_text(payload.get("candidate_hash"), "candidate_hash"),
            score=float(payload.get("score", 0.0)),
            trust_score=float(payload.get("trust_score", 0.0)),
            reliability_score=float(payload.get("reliability_score", 0.0)),
            route_efficiency=float(payload.get("route_efficiency", 0.0)),
            constraint_match=float(payload.get("constraint_match", 0.0)),
            anomaly_rate=float(payload.get("anomaly_rate", 0.0)),
            eligible=bool(payload.get("eligible", True)),
            explanation=tuple(str(value) for value in payload.get("explanation", ())),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "anomaly_rate": round(self.anomaly_rate, 6),
            "candidate_hash": self.candidate_hash,
            "constraint_match": round(self.constraint_match, 6),
            "eligible": self.eligible,
            "explanation": list(self.explanation),
            "participant_id": self.participant_id,
            "reliability_score": round(self.reliability_score, 6),
            "route_efficiency": round(self.route_efficiency, 6),
            "score": round(self.score, 6),
            "trust_score": round(self.trust_score, 6),
        }


@dataclass(frozen=True)
class DispatchDecision:
    request: DispatchRequest
    selected_participant_id: str
    ranked_candidates: tuple[DispatchRankedCandidate, ...]
    evidence: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    @property
    def authority_boundary(self) -> str:
        return AUTHORITY_BOUNDARY

    @property
    def schema(self) -> str:
        return SCHEMA

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence": dict(self.evidence),
            "ranked_candidates": [candidate.canonical_dict() for candidate in self.ranked_candidates],
            "request_hash": self.request.request_hash(),
            "schema": self.schema,
            "selected_participant_id": self.selected_participant_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["decision_hash"] = _canonical_hash(payload)
        payload["verified"] = self.verified
        return payload

    @property
    def decision_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    @property
    def verified(self) -> bool:
        return (
            len(self.decision_hash) == 64
            and self.selected_participant_id in {candidate.participant_id for candidate in self.ranked_candidates}
            and bool(self.ranked_candidates)
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DispatchDecision":
        if not isinstance(payload, Mapping):
            raise DispatchDecisionError("dispatch decision payload must be a mapping")
        request_payload = payload.get("request")
        if not isinstance(request_payload, Mapping):
            raise DispatchDecisionError("dispatch decision request payload is required")
        ranked = payload.get("ranked_candidates")
        if not isinstance(ranked, list) or not ranked:
            raise DispatchDecisionError("dispatch decision ranked_candidates are required")
        return cls(
            request=DispatchRequest.from_mapping(request_payload),
            selected_participant_id=_require_text(payload.get("selected_participant_id"), "selected_participant_id"),
            ranked_candidates=tuple(DispatchRankedCandidate.from_mapping(item) for item in ranked),
            evidence=_freeze_mapping(payload.get("evidence", {})),
        )


@dataclass(frozen=True)
class DispatchValidationReport:
    request_hash: str
    decision_hash: str
    expected_decision_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "decision_hash": self.decision_hash,
            "expected_decision_hash": self.expected_decision_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "request_hash": self.request_hash,
            "schema": "afritech.mobility.dispatch_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_trust_aware_dispatch(
    request: DispatchRequest | Mapping[str, Any],
    candidates: Iterable[DispatchCandidate | Mapping[str, Any]],
) -> DispatchDecision:
    normalized_request = request if isinstance(request, DispatchRequest) else DispatchRequest.from_mapping(request)
    normalized_candidates = tuple(
        candidate if isinstance(candidate, DispatchCandidate) else DispatchCandidate.from_mapping(candidate)
        for candidate in candidates
    )
    if not normalized_candidates:
        raise DispatchDecisionError("at least one candidate is required")

    ranked = _rank_candidates(normalized_request, normalized_candidates)
    if not ranked:
        raise DispatchDecisionError("no eligible dispatch candidates")

    selected = ranked[0].participant_id
    evidence = _build_evidence(normalized_request, normalized_candidates, ranked, selected)
    return DispatchDecision(
        request=normalized_request,
        selected_participant_id=selected,
        ranked_candidates=ranked,
        evidence=evidence,
    )


def validate_dispatch_decision(
    request: DispatchRequest | Mapping[str, Any],
    candidates: Iterable[DispatchCandidate | Mapping[str, Any]],
    decision: DispatchDecision | Mapping[str, Any],
) -> DispatchValidationReport:
    import importlib

    normalized_request = request if isinstance(request, DispatchRequest) else DispatchRequest.from_mapping(request)
    normalized_candidates = tuple(
        candidate if isinstance(candidate, DispatchCandidate) else DispatchCandidate.from_mapping(candidate)
        for candidate in candidates
    )
    actual = decision if isinstance(decision, DispatchDecision) else _decision_from_mapping(normalized_request, decision)
    expected = run_trust_aware_dispatch(normalized_request, normalized_candidates)
    invariants = importlib.import_module("afritech.mobility.trust_dispatch_invariants")
    DispatchInvariantError = invariants.DispatchInvariantError
    evaluate_dispatch_invariants = invariants.evaluate_dispatch_invariants
    validate_dispatch_invariants = invariants.validate_dispatch_invariants
    invariant_report = evaluate_dispatch_invariants(normalized_request, normalized_candidates, actual)
    try:
        validate_dispatch_invariants(invariant_report)
    except DispatchInvariantError as exc:
        raise DispatchDecisionError(str(exc)) from exc

    if actual.canonical_dict() != expected.canonical_dict():
        raise DispatchDecisionError("dispatch decision mismatch")

    if actual.decision_hash != expected.decision_hash:
        raise DispatchDecisionError("dispatch decision hash mismatch")

    expected_hash = expected.decision_hash
    report = DispatchValidationReport(
        request_hash=normalized_request.request_hash(),
        decision_hash=actual.decision_hash,
        expected_decision_hash=expected_hash,
        invariant_report_hash=invariant_report.report_hash(),
        verified=actual.decision_hash == expected_hash and invariant_report.verified,
    )
    if not report.verified:
        raise DispatchDecisionError("dispatch decision failed validation")
    return report


def build_dispatch_decision_proof(
    decision: DispatchDecision,
    request: DispatchRequest | None = None,
    candidates: Iterable[DispatchCandidate] | None = None,
) -> dict[str, Any]:
    request_payload = request or decision.request
    candidate_list = tuple(candidates or tuple())
    candidate_hashes = [candidate.candidate_hash() for candidate in candidate_list] if candidate_list else [
        item["candidate_hash"] for item in decision.canonical_dict()["ranked_candidates"]
    ]
    proof = {
        "schema": "afritech.mobility.dispatch_decision_proof.v1",
        "authority_boundary": "dispatch_proof_read_only",
        "input_hash": request_payload.request_hash() if isinstance(request_payload, DispatchRequest) else DispatchRequest.from_mapping(request_payload).request_hash(),
        "candidate_hashes": candidate_hashes,
        "selected_id": decision.selected_participant_id,
        "decision_hash": decision.decision_hash,
        "verified": decision.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def export_dispatch_decision_proof(
    decision: DispatchDecision,
    output_dir: str | Path,
) -> dict[str, Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "dispatch_decision_proof.json"
    json_path.write_text(
        json.dumps(build_dispatch_decision_proof(decision), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path}


def _rank_candidates(
    request: DispatchRequest,
    candidates: tuple[DispatchCandidate, ...],
) -> tuple[DispatchRankedCandidate, ...]:
    eligible = [
        _score_candidate(request, candidate)
        for candidate in candidates
        if candidate.availability and _is_eligible(request, candidate)
    ]
    ranked = sorted(
        eligible,
        key=lambda item: (
            -item.score,
            -item.trust_score,
            -item.reliability_score,
            -item.route_efficiency,
            item.anomaly_rate,
            item.participant_id,
        ),
    )
    return tuple(ranked)


def _score_candidate(request: DispatchRequest, candidate: DispatchCandidate) -> DispatchRankedCandidate:
    trust = _normalize_score(candidate.participant.trust_score)
    reliability = _normalize_score(candidate.reliability_score)
    route_efficiency = _route_efficiency(request, candidate.location)
    constraint_match = _constraint_match(request, candidate)
    anomaly = _normalize_score(candidate.anomaly_rate)
    score = _clamp(
        0.35 * trust
        + 0.25 * reliability
        + 0.20 * route_efficiency
        + 0.15 * constraint_match
        - 0.05 * anomaly
    )
    explanation = (
        f"trust={trust:.6f}",
        f"reliability={reliability:.6f}",
        f"route_efficiency={route_efficiency:.6f}",
        f"constraint_match={constraint_match:.6f}",
        f"anomaly_rate={anomaly:.6f}",
    )
    return DispatchRankedCandidate(
        participant_id=candidate.candidate_id,
        candidate_hash=candidate.candidate_hash(),
        score=score,
        trust_score=trust,
        reliability_score=reliability,
        route_efficiency=route_efficiency,
        constraint_match=constraint_match,
        anomaly_rate=anomaly,
        eligible=True,
        explanation=explanation,
    )


def _normalize_score(value: float) -> float:
    return _clamp(value / 100.0)


def _route_efficiency(request: DispatchRequest, location: GeoPoint) -> float:
    origin_distance = _haversine_km(location, request.origin)
    destination_distance = _haversine_km(location, request.destination)
    average_distance = (origin_distance + destination_distance) / 2.0
    return _clamp(1.0 - min(average_distance / 100.0, 1.0))


def _constraint_match(request: DispatchRequest, candidate: DispatchCandidate) -> float:
    constraints = request.constraint_map
    required_roles = tuple()
    required_operations = tuple()
    minimum_capacity = 1
    if constraints:
        if "required_roles" in constraints:
            required_roles = _normalize_roles(constraints["required_roles"])
        if "required_operations" in constraints:
            required_operations = _normalize_operations(constraints["required_operations"])
        if "minimum_capacity" in constraints:
            minimum_capacity = int(constraints["minimum_capacity"])
            if minimum_capacity < 1:
                raise DispatchDecisionError("minimum_capacity must be positive")

    satisfied = 0
    total = 0

    if required_roles:
        total += 1
        if set(required_roles) & set(candidate.participant.roles):
            satisfied += 1
    if required_operations:
        total += 1
        if request.operation_type in candidate.supported_operations or request.operation_type in required_operations:
            satisfied += 1
    if "minimum_capacity" in constraints:
        total += 1
        if candidate.capacity >= minimum_capacity:
            satisfied += 1
    if total == 0:
        return 1.0
    return _clamp(satisfied / total)


def _is_eligible(request: DispatchRequest, candidate: DispatchCandidate) -> bool:
    constraints = request.constraint_map
    if "required_roles" in constraints:
        required_roles = _normalize_roles(constraints["required_roles"])
        if not set(required_roles) & set(candidate.participant.roles):
            return False
    if "required_operations" in constraints:
        required_operations = _normalize_operations(constraints["required_operations"])
        if request.operation_type not in candidate.supported_operations and request.operation_type not in required_operations:
            return False
    if "minimum_capacity" in constraints:
        minimum_capacity = int(constraints["minimum_capacity"])
        if candidate.capacity < minimum_capacity:
            return False
    if candidate.supported_operations and request.operation_type not in candidate.supported_operations:
        return False
    return True


def _build_evidence(
    request: DispatchRequest,
    candidates: tuple[DispatchCandidate, ...],
    ranked: tuple[DispatchRankedCandidate, ...],
    selected: str,
) -> tuple[tuple[str, Any], ...]:
    payload = {
        "candidate_hashes": [candidate.candidate_hash() for candidate in candidates],
        "constraint_summary": request.constraint_map,
        "formula": "0.35*trust + 0.25*reliability + 0.20*route_efficiency + 0.15*constraint_match - 0.05*anomaly",
        "input_hash": request.request_hash(),
        "operation_id": request.operation_id,
        "operation_type": request.operation_type,
        "ranked_candidate_ids": [candidate.participant_id for candidate in ranked],
        "ranked_candidate_hashes": [candidate.candidate_hash for candidate in ranked],
        "selected_id": selected,
        "timestamp": request.timestamp,
    }
    return _freeze_mapping(payload)


def _decision_from_mapping(
    request: DispatchRequest,
    payload: Mapping[str, Any],
) -> DispatchDecision:
    if not isinstance(payload, Mapping):
        raise DispatchDecisionError("decision payload must be a mapping")
    ranked = payload.get("ranked_candidates")
    if not isinstance(ranked, list) or not ranked:
        raise DispatchDecisionError("decision ranked_candidates are required")
    ranked_candidates = []
    for item in ranked:
        if not isinstance(item, Mapping):
            raise DispatchDecisionError("ranked candidate must be mapping")
        ranked_candidates.append(
            DispatchRankedCandidate(
                participant_id=_require_text(item.get("participant_id"), "participant_id"),
                candidate_hash=_require_text(item.get("candidate_hash"), "candidate_hash"),
                score=float(item.get("score", 0.0)),
                trust_score=float(item.get("trust_score", 0.0)),
                reliability_score=float(item.get("reliability_score", 0.0)),
                route_efficiency=float(item.get("route_efficiency", 0.0)),
                constraint_match=float(item.get("constraint_match", 0.0)),
                anomaly_rate=float(item.get("anomaly_rate", 0.0)),
                eligible=bool(item.get("eligible", True)),
                explanation=tuple(str(value) for value in item.get("explanation", ())),
            )
        )
    evidence = _freeze_mapping(payload.get("evidence", {}))
    return DispatchDecision(
        request=request,
        selected_participant_id=_require_text(payload.get("selected_participant_id"), "selected_participant_id"),
        ranked_candidates=tuple(ranked_candidates),
        evidence=evidence,
    )


__all__ = [
    "AUTHORITY_BOUNDARY",
    "SCHEMA",
    "DispatchRequestError",
    "DispatchCandidateError",
    "DispatchDecisionError",
    "DispatchRequest",
    "DispatchCandidate",
    "DispatchRankedCandidate",
    "DispatchDecision",
    "DispatchValidationReport",
    "build_dispatch_decision_proof",
    "export_dispatch_decision_proof",
    "run_trust_aware_dispatch",
    "validate_dispatch_decision",
]
