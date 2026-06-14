"""Autonomous fleet governance for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant


SCHEMA = "afritech.mobility.fleet_governance.v1"
AUTHORITY_BOUNDARY = "fleet_governance_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "fleet_governance_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "fleet_governance_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "fleet_governance_proof_read_only"

ALLOWED_FLEET_TYPES = ("commercial", "institutional", "autonomous", "hybrid")
ALLOWED_VEHICLE_TYPES = ("ev", "bike", "drone", "autonomous", "car", "van", "truck")
ALLOWED_VEHICLE_STATUSES = ("available", "in_service", "maintenance", "suspended")
ALLOWED_OPERATOR_ROLES = {"fleet", "institution"}

FLEET_INVARIANT_IDS = (
    "IA-FLEET-001",
    "IA-FLEET-002",
    "IA-FLEET-003",
    "IA-FLEET-004",
    "IA-FLEET-005",
    "IA-FLEET-006",
)


class FleetGovernanceError(ValueError):
    """Raised when fleet governance payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FleetGovernanceError(f"{label} is required")
    return value.strip()


def _require_hash(value: object, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64:
        raise FleetGovernanceError(f"{label} must be a 64-character hex digest")
    return value


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or value < minimum:
        raise FleetGovernanceError(f"{label} must be an integer >= {minimum}")
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
        raise FleetGovernanceError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise FleetGovernanceError(f"{label} must be between {minimum} and {maximum}")
    return round(number, precision)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


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
        raise FleetGovernanceError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_links(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise FleetGovernanceError("evidence_links must be iterable")
    normalized = tuple(_require_text(value, "evidence_link") for value in values)
    return tuple(sorted(set(normalized)))


def _normalize_records(values: Iterable[object]) -> tuple["FleetMaintenanceRecord", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise FleetGovernanceError("maintenance_history must be iterable")
    records: list[FleetMaintenanceRecord] = []
    for item in values:
        if isinstance(item, FleetMaintenanceRecord):
            records.append(item)
        elif isinstance(item, Mapping):
            records.append(FleetMaintenanceRecord.from_mapping(item))
        else:
            raise FleetGovernanceError("maintenance_history must contain mappings or FleetMaintenanceRecord objects")
    return tuple(sorted(records, key=lambda record: (record.timestamp, record.maintenance_id)))


def _normalize_vehicles(values: Iterable[object]) -> tuple["FleetVehicle", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise FleetGovernanceError("vehicles must be iterable")
    vehicles: list[FleetVehicle] = []
    for item in values:
        if isinstance(item, FleetVehicle):
            vehicles.append(item)
        elif isinstance(item, Mapping):
            vehicles.append(FleetVehicle.from_mapping(item))
        else:
            raise FleetGovernanceError("vehicles must contain mappings or FleetVehicle objects")
    return tuple(sorted(vehicles, key=lambda vehicle: vehicle.vehicle_id))


def _vehicle_maintenance_score(vehicle: "FleetVehicle", fleet_timestamp: int) -> float:
    latest_timestamp = max(record.timestamp for record in vehicle.maintenance_history)
    if latest_timestamp > fleet_timestamp:
        raise FleetGovernanceError("maintenance history cannot be newer than fleet timestamp")
    age = max(0, fleet_timestamp - latest_timestamp)
    freshness = max(0.0, 1.0 - min(age, 31_536_000) / 31_536_000.0)
    density = min(1.0, len(vehicle.maintenance_history) / 3.0)
    return round((0.65 * freshness + 0.35 * density) * 100.0, 6)


def _vehicle_operational_score(vehicle: "FleetVehicle") -> float:
    return round(
        (vehicle.battery_health + vehicle.safety_score + vehicle.route_compliance_score) / 3.0,
        6,
    )


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 6)))


@dataclass(frozen=True)
class FleetMaintenanceRecord:
    maintenance_id: str
    timestamp: int
    service_type: str
    service_center_id: str
    custody_link: str
    evidence_link: str
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "maintenance_id", _require_text(self.maintenance_id, "maintenance_id"))
        object.__setattr__(self, "timestamp", _require_int(self.timestamp, "timestamp"))
        object.__setattr__(self, "service_type", _require_text(self.service_type, "service_type"))
        object.__setattr__(self, "service_center_id", _require_text(self.service_center_id, "service_center_id"))
        object.__setattr__(self, "custody_link", _require_text(self.custody_link, "custody_link"))
        object.__setattr__(self, "evidence_link", _require_text(self.evidence_link, "evidence_link"))
        if not isinstance(self.verified, bool) or not self.verified:
            raise FleetGovernanceError("maintenance records must be verified")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FleetMaintenanceRecord":
        if not isinstance(payload, Mapping):
            raise FleetGovernanceError("maintenance payload must be a mapping")
        return cls(
            maintenance_id=_require_text(payload.get("maintenance_id") or payload.get("id"), "maintenance_id"),
            timestamp=int(payload.get("timestamp", 0)),
            service_type=_require_text(payload.get("service_type"), "service_type"),
            service_center_id=_require_text(payload.get("service_center_id"), "service_center_id"),
            custody_link=_require_text(payload.get("custody_link") or payload.get("custody"), "custody_link"),
            evidence_link=_require_text(payload.get("evidence_link") or payload.get("evidence"), "evidence_link"),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    @property
    def maintenance_hash(self) -> str:
        payload = {
            "custody_link": self.custody_link,
            "evidence_link": self.evidence_link,
            "maintenance_id": self.maintenance_id,
            "metadata": dict(self.metadata),
            "service_center_id": self.service_center_id,
            "service_type": self.service_type,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }
        return _canonical_hash(payload)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "custody_link": self.custody_link,
            "evidence_link": self.evidence_link,
            "maintenance_hash": self.maintenance_hash,
            "maintenance_id": self.maintenance_id,
            "metadata": dict(self.metadata),
            "service_center_id": self.service_center_id,
            "service_type": self.service_type,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class FleetVehicle:
    vehicle_id: str
    vehicle_type: str
    status: str
    battery_health: float
    safety_score: float
    route_compliance_score: float
    maintenance_history: tuple[FleetMaintenanceRecord, ...] = field(default_factory=tuple)
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "vehicle_id", _require_text(self.vehicle_id, "vehicle_id"))
        if self.vehicle_type not in ALLOWED_VEHICLE_TYPES:
            raise FleetGovernanceError(f"unsupported vehicle_type: {self.vehicle_type}")
        object.__setattr__(self, "status", _require_text(self.status, "status"))
        if self.status not in ALLOWED_VEHICLE_STATUSES:
            raise FleetGovernanceError(f"unsupported vehicle status: {self.status}")
        object.__setattr__(self, "battery_health", _require_number(self.battery_health, "battery_health", minimum=0.0, maximum=100.0))
        object.__setattr__(self, "safety_score", _require_number(self.safety_score, "safety_score", minimum=0.0, maximum=100.0))
        object.__setattr__(self, "route_compliance_score", _require_number(self.route_compliance_score, "route_compliance_score", minimum=0.0, maximum=100.0))
        maintenance_history = _normalize_records(self.maintenance_history)
        if not maintenance_history:
            raise FleetGovernanceError("maintenance_history is required")
        object.__setattr__(self, "maintenance_history", maintenance_history)
        object.__setattr__(self, "evidence_links", _normalize_links(self.evidence_links))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FleetVehicle":
        if not isinstance(payload, Mapping):
            raise FleetGovernanceError("vehicle payload must be a mapping")
        return cls(
            vehicle_id=_require_text(payload.get("vehicle_id") or payload.get("id"), "vehicle_id"),
            vehicle_type=_require_text(payload.get("vehicle_type"), "vehicle_type"),
            status=_require_text(payload.get("status"), "status"),
            battery_health=float(payload.get("battery_health", 0.0)),
            safety_score=float(payload.get("safety_score", 0.0)),
            route_compliance_score=float(payload.get("route_compliance_score", 0.0)),
            maintenance_history=tuple(payload.get("maintenance_history", ())),  # type: ignore[arg-type]
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def vehicle_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    @property
    def operational_score(self) -> float:
        return _vehicle_operational_score(self)

    @property
    def eligible_for_dispatch(self) -> bool:
        return self.status == "available" and self.operational_score >= 70.0

    def maintenance_score(self, fleet_timestamp: int) -> float:
        return _vehicle_maintenance_score(self, fleet_timestamp)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "battery_health": round(self.battery_health, 6),
            "evidence_links": list(self.evidence_links),
            "maintenance_history": [record.canonical_dict() for record in self.maintenance_history],
            "metadata": dict(self.metadata),
            "operational_score": self.operational_score,
            "route_compliance_score": round(self.route_compliance_score, 6),
            "safety_score": round(self.safety_score, 6),
            "status": self.status,
            "vehicle_hash": self.vehicle_hash,
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "verified": self.verified,
        }

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "battery_health": round(self.battery_health, 6),
            "evidence_links": list(self.evidence_links),
            "maintenance_history": [record.canonical_dict() for record in self.maintenance_history],
            "metadata": dict(self.metadata),
            "route_compliance_score": round(self.route_compliance_score, 6),
            "safety_score": round(self.safety_score, 6),
            "status": self.status,
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
        }

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and len(self.vehicle_hash) == 64 and all(record.verified for record in self.maintenance_history)


@dataclass(frozen=True)
class FleetState:
    fleet_id: str
    operator: MobilityParticipant
    region_id: str
    fleet_type: str
    vehicles: tuple[FleetVehicle, ...] = field(default_factory=tuple)
    timestamp: int = 0
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "fleet_id", _require_text(self.fleet_id, "fleet_id"))
        if not isinstance(self.operator, MobilityParticipant):
            raise FleetGovernanceError("operator must be a MobilityParticipant")
        if not any(role in ALLOWED_OPERATOR_ROLES for role in self.operator.roles):
            raise FleetGovernanceError("operator must have a fleet or institution role")
        object.__setattr__(self, "region_id", _require_text(self.region_id, "region_id"))
        if self.fleet_type not in ALLOWED_FLEET_TYPES:
            raise FleetGovernanceError(f"unsupported fleet_type: {self.fleet_type}")
        object.__setattr__(self, "vehicles", _normalize_vehicles(self.vehicles))
        if not self.vehicles:
            raise FleetGovernanceError("at least one vehicle is required")
        object.__setattr__(self, "timestamp", _require_int(self.timestamp, "timestamp"))
        object.__setattr__(self, "evidence_links", _normalize_links(self.evidence_links))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FleetState":
        if not isinstance(payload, Mapping):
            raise FleetGovernanceError("fleet state payload must be a mapping")
        operator = payload.get("operator")
        if not isinstance(operator, MobilityParticipant):
            operator = MobilityParticipant.from_mapping(operator or {})
        return cls(
            fleet_id=_require_text(payload.get("fleet_id") or payload.get("id"), "fleet_id"),
            operator=operator,
            region_id=_require_text(payload.get("region_id"), "region_id"),
            fleet_type=_require_text(payload.get("fleet_type", "commercial"), "fleet_type"),
            vehicles=tuple(payload.get("vehicles", ())),  # type: ignore[arg-type]
            timestamp=int(payload.get("timestamp", 0)),
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def fleet_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence_links": list(self.evidence_links),
            "fleet_id": self.fleet_id,
            "fleet_type": self.fleet_type,
            "metadata": dict(self.metadata),
            "operator": self.operator.canonical_dict(),
            "region_id": self.region_id,
            "schema": SCHEMA,
            "timestamp": self.timestamp,
            "vehicles": [vehicle.canonical_dict() for vehicle in self.vehicles],
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence_links": list(self.evidence_links),
            "fleet_hash": self.fleet_hash,
            "fleet_id": self.fleet_id,
            "fleet_type": self.fleet_type,
            "metadata": dict(self.metadata),
            "operator": self.operator.canonical_dict(),
            "region_id": self.region_id,
            "schema": SCHEMA,
            "timestamp": self.timestamp,
            "vehicles": [vehicle.canonical_dict() for vehicle in self.vehicles],
            "verified": self.verified,
        }

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and len(self.fleet_hash) == 64 and len(self.operator.participant_hash()) == 64 and all(vehicle.verified for vehicle in self.vehicles)


@dataclass(frozen=True)
class FleetGovernanceReport:
    fleet_id: str
    region_id: str
    fleet_hash: str
    operator_id: str
    operator_hash: str
    fleet_trust_score: float
    vehicle_health_score: float
    maintenance_score: float
    eligible_vehicle_ids: tuple[str, ...]
    vehicle_reports: tuple[tuple[str, Any], ...]
    evidence: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and len(self.fleet_hash) == 64 and len(self.operator_hash) == 64 and 0.0 <= self.fleet_trust_score <= 100.0

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence": dict(self.evidence),
            "eligible_vehicle_ids": list(self.eligible_vehicle_ids),
            "fleet_hash": self.fleet_hash,
            "fleet_id": self.fleet_id,
            "fleet_trust_score": round(self.fleet_trust_score, 6),
            "maintenance_score": round(self.maintenance_score, 6),
            "operator_hash": self.operator_hash,
            "operator_id": self.operator_id,
            "region_id": self.region_id,
            "schema": "afritech.mobility.fleet_governance_report.v1",
            "vehicle_health_score": round(self.vehicle_health_score, 6),
            "vehicle_reports": [
                {"details": details, "vehicle_id": vehicle_id}
                for vehicle_id, details in self.vehicle_reports
            ],
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class FleetInvariantCheck:
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
class FleetInvariantReport:
    fleet_hash: str
    report_hash: str
    proof_hash: str
    checks: tuple[FleetInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "checks": [check.canonical_dict() for check in self.checks],
            "fleet_hash": self.fleet_hash,
            "proof_hash": self.proof_hash,
            "report_hash": self.report_hash,
            "schema": "afritech.mobility.fleet_invariant_report.v1",
            "verified": self.verified,
        }

    def report_hash_value(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class FleetValidationReport:
    fleet_hash: str
    report_hash: str
    invariant_report_hash: str
    proof_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "fleet_hash": self.fleet_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "report_hash": self.report_hash,
            "schema": "afritech.mobility.fleet_validation_report.v1",
            "verified": self.verified,
        }


def build_fleet_governance(state: FleetState | Mapping[str, Any]) -> FleetGovernanceReport:
    normalized = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    vehicle_reports: list[tuple[str, Any]] = []
    vehicle_health_scores: list[float] = []
    maintenance_scores: list[float] = []
    eligible_vehicle_ids: list[str] = []
    for vehicle in normalized.vehicles:
        operational_score = vehicle.operational_score
        maintenance_score = vehicle.maintenance_score(normalized.timestamp)
        vehicle_health_scores.append(operational_score)
        maintenance_scores.append(maintenance_score)
        vehicle_reports.append(
            (
                vehicle.vehicle_id,
                {
                    "battery_health": round(vehicle.battery_health, 6),
                    "maintenance_hash": [record.maintenance_hash for record in vehicle.maintenance_history],
                    "maintenance_score": round(maintenance_score, 6),
                    "operational_score": round(operational_score, 6),
                    "route_compliance_score": round(vehicle.route_compliance_score, 6),
                    "safety_score": round(vehicle.safety_score, 6),
                    "status": vehicle.status,
                    "vehicle_hash": vehicle.vehicle_hash,
                    "verified": vehicle.verified,
                },
            )
        )
        if vehicle.eligible_for_dispatch:
            eligible_vehicle_ids.append(vehicle.vehicle_id)
    operator_score = normalized.operator.trust_score
    average_vehicle_health = sum(vehicle_health_scores) / len(vehicle_health_scores)
    average_maintenance = sum(maintenance_scores) / len(maintenance_scores)
    dispatch_ready_ratio = len(eligible_vehicle_ids) / len(normalized.vehicles)
    fleet_trust_score = _clamp_score(
        0.30 * operator_score
        + 0.35 * average_vehicle_health
        + 0.20 * average_maintenance
        + 0.15 * (dispatch_ready_ratio * 100.0)
    )
    evidence = {
        "dispatch_ready_ratio": round(dispatch_ready_ratio, 6),
        "fleet_hash": normalized.fleet_hash,
        "operator_trust_score": round(operator_score, 6),
        "vehicle_count": len(normalized.vehicles),
        "vehicle_hashes": [vehicle.vehicle_hash for vehicle in normalized.vehicles],
    }
    return FleetGovernanceReport(
        fleet_id=normalized.fleet_id,
        region_id=normalized.region_id,
        fleet_hash=normalized.fleet_hash,
        operator_id=normalized.operator.participant_id,
        operator_hash=normalized.operator.participant_hash(),
        fleet_trust_score=fleet_trust_score,
        vehicle_health_score=_clamp_score(average_vehicle_health),
        maintenance_score=_clamp_score(average_maintenance),
        eligible_vehicle_ids=tuple(sorted(set(eligible_vehicle_ids))),
        vehicle_reports=tuple(sorted(vehicle_reports, key=lambda item: item[0])),
        evidence=tuple(sorted(evidence.items(), key=lambda item: item[0])),
    )


def validate_fleet_governance(
    state: FleetState | Mapping[str, Any],
    report: FleetGovernanceReport | Mapping[str, Any] | None = None,
) -> FleetValidationReport:
    normalized_state = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    actual = _coerce_report(report, normalized_state)
    expected = build_fleet_governance(normalized_state)
    invariant_report = evaluate_fleet_invariants(normalized_state, actual)
    validate_fleet_invariants(invariant_report)
    if actual.canonical_dict() != expected.canonical_dict():
        raise FleetGovernanceError("fleet governance report mismatch")
    if actual.report_hash() != expected.report_hash():
        raise FleetGovernanceError("fleet governance report hash mismatch")
    proof = _fleet_proof_payload(normalized_state, actual, verified=actual.verified and invariant_report.verified)
    return FleetValidationReport(
        fleet_hash=normalized_state.fleet_hash,
        report_hash=actual.report_hash(),
        invariant_report_hash=invariant_report.report_hash,
        proof_hash=proof["proof_hash"],
        verified=proof["verified"],
    )


def build_fleet_governance_proof(
    state: FleetState | Mapping[str, Any],
    report: FleetGovernanceReport | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_state = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    actual = _coerce_report(report, normalized_state)
    validation = validate_fleet_governance(normalized_state, actual)
    return _fleet_proof_payload(normalized_state, actual, verified=validation.verified)


def export_fleet_governance_proof(
    state: FleetState | Mapping[str, Any],
    output_dir: str | Path,
    report: FleetGovernanceReport | Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    normalized_state = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    actual = _coerce_report(report, normalized_state)
    proof = build_fleet_governance_proof(normalized_state, actual)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "fleet_governance_state.json"
    proof_path = target / "fleet_governance_proof.json"
    state_path.write_text(json.dumps(normalized_state.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def evaluate_fleet_invariants(
    state: FleetState | Mapping[str, Any],
    report: FleetGovernanceReport | Mapping[str, Any] | None = None,
) -> FleetInvariantReport:
    normalized_state = state if isinstance(state, FleetState) else FleetState.from_mapping(state)
    actual = _coerce_report(report, normalized_state)
    expected = build_fleet_governance(normalized_state)
    checks = (
        _check_maintenance_traceable(normalized_state),
        _check_trust_derived(actual, expected),
        _check_replayable(normalized_state, actual, expected),
        _check_custody_explicit(normalized_state, actual),
        _check_trust_bounds(actual),
        _check_authority_boundary(normalized_state, actual),
    )
    proof = _fleet_proof_payload(normalized_state, actual, verified=normalized_state.verified and actual.verified and all(check.satisfied for check in checks))
    return FleetInvariantReport(
        fleet_hash=normalized_state.fleet_hash,
        report_hash=actual.report_hash(),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_fleet_invariants(report: FleetInvariantReport) -> bool:
    if not isinstance(report, FleetInvariantReport):
        raise FleetGovernanceError("report must be a FleetInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise FleetGovernanceError("fleet invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in FLEET_INVARIANT_IDS if identifier not in observed)
    if missing:
        raise FleetGovernanceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise FleetGovernanceError(f"{check.identifier} failed: {check.details}")
    return True


def validate_fleet_governance_report(report: FleetGovernanceReport) -> bool:
    if not isinstance(report, FleetGovernanceReport):
        raise FleetGovernanceError("report must be a FleetGovernanceReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise FleetGovernanceError("fleet governance authority boundary mismatch")
    return report.verified


def _coerce_report(
    report: FleetGovernanceReport | Mapping[str, Any] | None,
    state: FleetState,
) -> FleetGovernanceReport:
    if report is None:
        return build_fleet_governance(state)
    if isinstance(report, FleetGovernanceReport):
        return report
    if not isinstance(report, Mapping):
        raise FleetGovernanceError("report must be a mapping or FleetGovernanceReport")
    vehicle_reports = tuple(
        (entry["vehicle_id"], entry["details"])
        for entry in report.get("vehicle_reports", ())
    )
    evidence = report.get("evidence", {})
    if isinstance(evidence, Mapping):
        evidence_items = tuple(sorted((str(key), _freeze_value(val)) for key, val in evidence.items()))
    else:
        evidence_items = tuple(sorted((str(key), _freeze_value(val)) for key, val in evidence))
    return FleetGovernanceReport(
        fleet_id=_require_text(report.get("fleet_id"), "fleet_id"),
        region_id=_require_text(report.get("region_id"), "region_id"),
        fleet_hash=_require_text(report.get("fleet_hash"), "fleet_hash"),
        operator_id=_require_text(report.get("operator_id"), "operator_id"),
        operator_hash=_require_text(report.get("operator_hash"), "operator_hash"),
        fleet_trust_score=float(report.get("fleet_trust_score", 0.0)),
        vehicle_health_score=float(report.get("vehicle_health_score", 0.0)),
        maintenance_score=float(report.get("maintenance_score", 0.0)),
        eligible_vehicle_ids=tuple(report.get("eligible_vehicle_ids", ())),  # type: ignore[arg-type]
        vehicle_reports=vehicle_reports,
        evidence=evidence_items,
        authority_boundary=_require_text(report.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
    )


def _fleet_proof_payload(
    state: FleetState,
    report: FleetGovernanceReport,
    *,
    verified: bool,
) -> dict[str, Any]:
    proof = {
        "schema": "afritech.mobility.fleet_governance_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "fleet_id": state.fleet_id,
        "region_id": state.region_id,
        "fleet_hash": state.fleet_hash,
        "report_hash": report.report_hash(),
        "operator_id": state.operator.participant_id,
        "operator_hash": state.operator.participant_hash(),
        "fleet_trust_score": round(report.fleet_trust_score, 6),
        "eligible_vehicle_ids": list(report.eligible_vehicle_ids),
        "vehicle_hashes": [vehicle.vehicle_hash for vehicle in state.vehicles],
        "maintenance_hashes": [
            record.maintenance_hash
            for vehicle in state.vehicles
            for record in vehicle.maintenance_history
        ],
        "evidence": dict(report.evidence),
        "verified": verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def _check_maintenance_traceable(state: FleetState) -> FleetInvariantCheck:
    satisfied = all(
        vehicle.maintenance_history
        and all(record.custody_link and record.evidence_link and record.verified for record in vehicle.maintenance_history)
        for vehicle in state.vehicles
    )
    return FleetInvariantCheck(
        identifier="IA-FLEET-001",
        satisfied=satisfied,
        details="maintenance history is traceable",
        evidence_hash=state.fleet_hash,
    )


def _check_trust_derived(actual: FleetGovernanceReport, expected: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = actual.canonical_dict() == expected.canonical_dict() and 0.0 <= actual.fleet_trust_score <= 100.0
    return FleetInvariantCheck(
        identifier="IA-FLEET-002",
        satisfied=satisfied,
        details="fleet trust is derived from operator and vehicle evidence",
        evidence_hash=actual.report_hash(),
    )


def _check_replayable(state: FleetState, actual: FleetGovernanceReport, expected: FleetGovernanceReport) -> FleetInvariantCheck:
    round_tripped_state = FleetState.from_mapping(state.canonical_dict())
    satisfied = actual.canonical_dict() == expected.canonical_dict() and round_tripped_state.canonical_dict() == state.canonical_dict()
    return FleetInvariantCheck(
        identifier="IA-FLEET-003",
        satisfied=satisfied,
        details="vehicle state is replayable",
        evidence_hash=state.fleet_hash,
    )


def _check_custody_explicit(state: FleetState, report: FleetGovernanceReport) -> FleetInvariantCheck:
    custody_links = [
        record.custody_link
        for vehicle in state.vehicles
        for record in vehicle.maintenance_history
    ]
    eligible_ok = all(
        vehicle.vehicle_id in set(report.eligible_vehicle_ids)
        for vehicle in state.vehicles
        if vehicle.eligible_for_dispatch
    )
    satisfied = bool(custody_links) and eligible_ok and all(link.strip() for link in custody_links)
    return FleetInvariantCheck(
        identifier="IA-FLEET-004",
        satisfied=satisfied,
        details="custody and service evidence are explicit",
        evidence_hash=report.report_hash(),
    )


def _check_trust_bounds(report: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = 0.0 <= report.fleet_trust_score <= 100.0 and 0.0 <= report.vehicle_health_score <= 100.0 and 0.0 <= report.maintenance_score <= 100.0
    return FleetInvariantCheck(
        identifier="IA-FLEET-005",
        satisfied=satisfied,
        details="fleet trust remains bounded",
        evidence_hash=report.report_hash(),
    )


def _check_authority_boundary(state: FleetState, report: FleetGovernanceReport) -> FleetInvariantCheck:
    satisfied = state.authority_boundary == AUTHORITY_BOUNDARY and report.authority_boundary == AUTHORITY_BOUNDARY and state.verified and report.verified
    return FleetInvariantCheck(
        identifier="IA-FLEET-006",
        satisfied=satisfied,
        details="fleet governance preserves the authority boundary",
        evidence_hash=state.fleet_hash,
    )


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_fleet_governance":
        return build_fleet_governance
    raise AttributeError(name)


__all__ = [
    "ALLOWED_FLEET_TYPES",
    "ALLOWED_OPERATOR_ROLES",
    "ALLOWED_VEHICLE_STATUSES",
    "ALLOWED_VEHICLE_TYPES",
    "AUTHORITY_BOUNDARY",
    "FLEET_INVARIANT_IDS",
    "FleetGovernanceError",
    "FleetGovernanceReport",
    "FleetInvariantCheck",
    "FleetInvariantReport",
    "FleetMaintenanceRecord",
    "FleetState",
    "FleetValidationReport",
    "FleetVehicle",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_fleet_governance",
    "build_fleet_governance_proof",
    "evaluate_fleet_invariants",
    "export_fleet_governance_proof",
    "validate_fleet_governance",
    "validate_fleet_governance_report",
    "validate_fleet_invariants",
]

