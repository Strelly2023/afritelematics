"""Institutional mobility governance for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.fleet_governance import (
    AUTHORITY_BOUNDARY as FLEET_AUTHORITY_BOUNDARY,
    FleetGovernanceError,
    FleetGovernanceReport,
    validate_fleet_invariants,
)


SCHEMA = "afritech.mobility.institutional_network.v1"
AUTHORITY_BOUNDARY = "institution_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "institution_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "institution_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "institution_proof_read_only"
INSTITUTION_PROOF_AUTHORITY_BOUNDARY = PROOF_AUTHORITY_BOUNDARY

ALLOWED_DOMAIN_TYPES = (
    "hospital",
    "airport",
    "university",
    "campus",
    "government",
    "corporate",
    "logistics",
)

ALLOWED_POLICY_TYPES = ("dispatch", "access", "market", "custody")
INSTITUTION_POLICY_TYPES = ALLOWED_POLICY_TYPES

INSTITUTION_INVARIANT_IDS = (
    "IA-INSTITUTION-001",
    "IA-INSTITUTION-002",
    "IA-INSTITUTION-003",
    "IA-INSTITUTION-004",
    "IA-INSTITUTION-005",
    "IA-INSTITUTION-006",
)


class InstitutionGovernanceError(ValueError):
    """Raised when institutional governance payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InstitutionGovernanceError(f"{label} is required")
    return value.strip()


def _require_hash(value: object, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64:
        raise InstitutionGovernanceError(f"{label} must be a 64-character hex digest")
    return value


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or value < minimum:
        raise InstitutionGovernanceError(f"{label} must be an integer >= {minimum}")
    return value


def _require_number(value: object, label: str, *, minimum: float, maximum: float, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise InstitutionGovernanceError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise InstitutionGovernanceError(f"{label} must be between {minimum} and {maximum}")
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
        raise InstitutionGovernanceError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_text_tuple(values: Iterable[object], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise InstitutionGovernanceError(f"{label} must be iterable")
    normalized = tuple(_require_text(value, label[:-1] if label.endswith("s") else label) for value in values)
    return tuple(sorted(set(normalized)))


def _normalize_participants(values: Iterable[object]) -> tuple[MobilityParticipant, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise InstitutionGovernanceError("participants must be iterable")
    participants: list[MobilityParticipant] = []
    for item in values:
        if isinstance(item, MobilityParticipant):
            participants.append(item)
        elif isinstance(item, Mapping):
            participants.append(MobilityParticipant.from_mapping(item))
        else:
            raise InstitutionGovernanceError("participants must contain mappings or MobilityParticipant objects")
    return tuple(sorted(participants, key=lambda participant: participant.participant_id))


def _normalize_fleets(values: Iterable[object]) -> tuple[FleetGovernanceReport, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise InstitutionGovernanceError("fleets must be iterable")
    fleets: list[FleetGovernanceReport] = []
    for item in values:
        if isinstance(item, FleetGovernanceReport):
            fleets.append(item)
        elif isinstance(item, Mapping):
            fleets.append(_fleet_report_from_mapping(item))
        else:
            raise InstitutionGovernanceError("fleets must contain mappings or FleetGovernanceReport objects")
    return tuple(sorted(fleets, key=lambda report: report.fleet_id))


def _policy_constraints(value: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    return _freeze_mapping(value or {})


@dataclass(frozen=True)
class InstitutionPolicy:
    policy_id: str
    policy_type: str
    constraints: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    enforcement_rules: tuple[str, ...] = field(default_factory=tuple)
    verified: bool = True
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", _require_text(self.policy_id, "policy_id"))
        if self.policy_type not in ALLOWED_POLICY_TYPES:
            raise InstitutionGovernanceError(f"unsupported policy_type: {self.policy_type}")
        object.__setattr__(self, "constraints", _policy_constraints(dict(self.constraints)))
        object.__setattr__(self, "enforcement_rules", _normalize_text_tuple(self.enforcement_rules, "enforcement_rules"))
        if not isinstance(self.verified, bool) or not self.verified:
            raise InstitutionGovernanceError("institution policies must be verified")
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "InstitutionPolicy":
        if not isinstance(payload, Mapping):
            raise InstitutionGovernanceError("policy payload must be a mapping")
        return cls(
            policy_id=_require_text(payload.get("policy_id") or payload.get("id"), "policy_id"),
            policy_type=_require_text(payload.get("policy_type"), "policy_type"),
            constraints=_policy_constraints(payload.get("constraints", {})),
            enforcement_rules=tuple(payload.get("enforcement_rules", ())),  # type: ignore[arg-type]
            verified=bool(payload.get("verified", True)),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def policy_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "constraints": dict(self.constraints),
            "enforcement_rules": list(self.enforcement_rules),
            "policy_hash": self.policy_hash,
            "policy_id": self.policy_id,
            "policy_type": self.policy_type,
            "verified": self.verified,
        }

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "constraints": dict(self.constraints),
            "enforcement_rules": list(self.enforcement_rules),
            "policy_id": self.policy_id,
            "policy_type": self.policy_type,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class InstitutionNetwork:
    institution_id: str
    domain_type: str
    participants: tuple[MobilityParticipant, ...] = field(default_factory=tuple)
    fleets: tuple[FleetGovernanceReport, ...] = field(default_factory=tuple)
    policies: tuple[InstitutionPolicy, ...] = field(default_factory=tuple)
    timestamp: int = 0
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _require_text(self.institution_id, "institution_id"))
        if self.domain_type not in ALLOWED_DOMAIN_TYPES:
            raise InstitutionGovernanceError(f"unsupported domain_type: {self.domain_type}")
        object.__setattr__(self, "participants", _normalize_participants(self.participants))
        object.__setattr__(self, "fleets", _normalize_fleets(self.fleets))
        policies = tuple(
            sorted(
                (
                    item if isinstance(item, InstitutionPolicy) else InstitutionPolicy.from_mapping(item)
                    for item in self.policies
                ),
                key=lambda policy: policy.policy_id,
            )
        )
        object.__setattr__(self, "policies", policies)
        if not self.policies:
            raise InstitutionGovernanceError("at least one policy is required")
        object.__setattr__(self, "timestamp", _require_int(self.timestamp, "timestamp"))
        object.__setattr__(self, "evidence_links", tuple(sorted(set(_normalize_text_tuple(self.evidence_links, "evidence_links")))))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise InstitutionGovernanceError("institution authority boundary mismatch")
        for participant in self.participants:
            _validate_institution_metadata(participant, self.institution_id, "participant")
        for fleet in self.fleets:
            _validate_institution_metadata(fleet, self.institution_id, "fleet")
        _validate_membership_constraints(self)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "InstitutionNetwork":
        if not isinstance(payload, Mapping):
            raise InstitutionGovernanceError("institution payload must be a mapping")
        network = cls(
            institution_id=_require_text(payload.get("institution_id") or payload.get("id"), "institution_id"),
            domain_type=_require_text(payload.get("domain_type"), "domain_type"),
            participants=tuple(payload.get("participants", ())),  # type: ignore[arg-type]
            fleets=tuple(payload.get("fleets", ())),  # type: ignore[arg-type]
            policies=tuple(payload.get("policies", ())),  # type: ignore[arg-type]
            timestamp=int(payload.get("timestamp", 0)),
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )
        _validate_shadow_fields(payload, network)
        return network

    @property
    def reference_hash(self) -> str:
        payload = {
            "authority_boundary": self.authority_boundary,
            "domain_type": self.domain_type,
            "evidence_links": list(self.evidence_links),
            "institution_id": self.institution_id,
            "metadata": dict(self.metadata),
            "participant_hashes": [participant.participant_hash() for participant in self.participants],
            "fleet_hashes": [fleet.fleet_hash for fleet in self.fleets],
            "schema": SCHEMA,
            "timestamp": self.timestamp,
        }
        return _canonical_hash(payload)

    @property
    def governance_hash(self) -> str:
        return _canonical_hash(self._governance_payload())

    def _governance_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "domain_type": self.domain_type,
            "evidence_links": list(self.evidence_links),
            "fleets": [fleet.canonical_dict() for fleet in self.fleets],
            "institution_id": self.institution_id,
            "metadata": dict(self.metadata),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "policies": [policy.canonical_dict() for policy in self.policies],
            "schema": SCHEMA,
            "timestamp": self.timestamp,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "domain_type": self.domain_type,
            "evidence_links": list(self.evidence_links),
            "fleets": [fleet.canonical_dict() for fleet in self.fleets],
            "fleet_ids": [fleet.fleet_id for fleet in self.fleets],
            "fleet_hashes": [fleet.fleet_hash for fleet in self.fleets],
            "governance_hash": self.governance_hash,
            "institution_id": self.institution_id,
            "metadata": dict(self.metadata),
            "participants": [participant.canonical_dict() for participant in self.participants],
            "participant_ids": [participant.participant_id for participant in self.participants],
            "participant_hashes": [participant.participant_hash() for participant in self.participants],
            "policies": [policy.canonical_dict() for policy in self.policies],
            "policy_ids": [policy.policy_id for policy in self.policies],
            "policy_hashes": [policy.policy_hash for policy in self.policies],
            "reference_hash": self.reference_hash,
            "schema": SCHEMA,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.governance_hash) == 64
            and len(self.reference_hash) == 64
            and len(set(participant.participant_id for participant in self.participants)) == len(self.participants)
            and len(set(fleet.fleet_id for fleet in self.fleets)) == len(self.fleets)
            and all(participant.verification_status == "verified" for participant in self.participants)
            and all(fleet.verified for fleet in self.fleets)
            and all(policy.verified for policy in self.policies)
        )


@dataclass(frozen=True)
class InstitutionGovernanceReport:
    institution_id: str
    domain_type: str
    governance_hash: str
    reference_hash: str
    policy_hash: str
    dispatch_projection: tuple[str, ...]
    access_projection: tuple[str, ...]
    market_projection: tuple[str, ...]
    custody_projection: tuple[str, ...]
    participant_bindings: tuple[tuple[str, Any], ...]
    fleet_bindings: tuple[tuple[str, Any], ...]
    evidence: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == AUTHORITY_BOUNDARY and len(self.governance_hash) == 64 and len(self.reference_hash) == 64 and len(self.policy_hash) == 64

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "access_projection": list(self.access_projection),
            "authority_boundary": self.authority_boundary,
            "custody_projection": list(self.custody_projection),
            "dispatch_projection": list(self.dispatch_projection),
            "domain_type": self.domain_type,
            "evidence": dict(self.evidence),
            "fleet_bindings": [
                {"fleet_id": fleet_id, "details": details}
                for fleet_id, details in self.fleet_bindings
            ],
            "governance_hash": self.governance_hash,
            "institution_id": self.institution_id,
            "market_projection": list(self.market_projection),
            "participant_bindings": [
                {"participant_id": participant_id, "details": details}
                for participant_id, details in self.participant_bindings
            ],
            "policy_hash": self.policy_hash,
            "reference_hash": self.reference_hash,
            "schema": "afritech.mobility.institution_governance_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class InstitutionInvariantCheck:
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
class InstitutionInvariantReport:
    institution_hash: str
    report_hash: str
    proof_hash: str
    checks: tuple[InstitutionInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "checks": [check.canonical_dict() for check in self.checks],
            "institution_hash": self.institution_hash,
            "proof_hash": self.proof_hash,
            "report_hash": self.report_hash,
            "schema": "afritech.mobility.institution_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class InstitutionValidationReport:
    institution_hash: str
    report_hash: str
    invariant_report_hash: str
    proof_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "institution_hash": self.institution_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "report_hash": self.report_hash,
            "schema": "afritech.mobility.institution_validation_report.v1",
            "verified": self.verified,
        }


def build_institution_governance(network: InstitutionNetwork | Mapping[str, Any]) -> InstitutionGovernanceReport:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    participant_bindings = tuple(
        (participant.participant_id, _participant_binding_details(participant, normalized))
        for participant in normalized.participants
    )
    fleet_bindings = tuple(
        (fleet.fleet_id, _fleet_binding_details(fleet, normalized))
        for fleet in normalized.fleets
    )
    dispatch_projection = _dispatch_projection(normalized)
    access_projection = _access_projection(normalized)
    market_projection = _market_projection(normalized)
    custody_projection = _custody_projection(normalized)
    evidence = {
        "dispatch_projection_hash": _canonical_hash(dispatch_projection),
        "fleet_count": len(normalized.fleets),
        "institution_hash": normalized.governance_hash,
        "policy_count": len(normalized.policies),
        "policy_types": [policy.policy_type for policy in normalized.policies],
        "reference_hash": normalized.reference_hash,
    }
    return InstitutionGovernanceReport(
        institution_id=normalized.institution_id,
        domain_type=normalized.domain_type,
        governance_hash=normalized.governance_hash,
        reference_hash=normalized.reference_hash,
        policy_hash=_canonical_hash([policy.policy_hash for policy in normalized.policies]),
        dispatch_projection=dispatch_projection,
        access_projection=access_projection,
        market_projection=market_projection,
        custody_projection=custody_projection,
        participant_bindings=participant_bindings,
        fleet_bindings=fleet_bindings,
        evidence=tuple(sorted(evidence.items(), key=lambda item: item[0])),
    )


def validate_institution_governance(
    network: InstitutionNetwork | Mapping[str, Any],
    report: InstitutionGovernanceReport | Mapping[str, Any] | None = None,
) -> InstitutionValidationReport:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    actual = _coerce_report(report, normalized)
    expected = build_institution_governance(normalized)
    invariant_report = evaluate_institution_invariants(normalized, actual)
    validate_institution_invariants(invariant_report)
    if actual.canonical_dict() != expected.canonical_dict():
        raise InstitutionGovernanceError("institution governance report mismatch")
    if actual.report_hash() != expected.report_hash():
        raise InstitutionGovernanceError("institution governance report hash mismatch")
    proof = _institution_proof_payload(normalized, actual, verified=actual.verified and invariant_report.verified)
    return InstitutionValidationReport(
        institution_hash=normalized.governance_hash,
        report_hash=actual.report_hash(),
        invariant_report_hash=invariant_report.report_hash,
        proof_hash=proof["proof_hash"],
        verified=proof["verified"],
    )


def evaluate_institution_invariants(
    network: InstitutionNetwork | Mapping[str, Any],
    report: InstitutionGovernanceReport | Mapping[str, Any] | None = None,
) -> InstitutionInvariantReport:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    actual = _coerce_report(report, normalized)
    expected = build_institution_governance(normalized)
    checks = (
        _check_policies_hashable(normalized),
        _check_policies_replayable(normalized, actual, expected),
        _check_no_proof_override(normalized, actual),
        _check_dispatch_constraints_deterministic(normalized, actual),
        _check_boundaries_enforceable(normalized, actual),
        _check_unique_identities(normalized),
    )
    proof = _institution_proof_payload(normalized, actual, verified=normalized.verified and actual.verified and all(check.satisfied for check in checks))
    return InstitutionInvariantReport(
        institution_hash=normalized.governance_hash,
        report_hash=actual.report_hash(),
        proof_hash=proof["proof_hash"],
        checks=checks,
    )


def validate_institution_invariants(report: InstitutionInvariantReport) -> bool:
    if not isinstance(report, InstitutionInvariantReport):
        raise InstitutionGovernanceError("report must be an InstitutionInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise InstitutionGovernanceError("institution invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INSTITUTION_INVARIANT_IDS if identifier not in observed)
    if missing:
        raise InstitutionGovernanceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise InstitutionGovernanceError(f"{check.identifier} failed: {check.details}")
    return True


def build_institution_governance_proof(
    network: InstitutionNetwork | Mapping[str, Any],
    report: InstitutionGovernanceReport | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    actual = _coerce_report(report, normalized)
    validation = validate_institution_governance(normalized, actual)
    return _institution_proof_payload(normalized, actual, verified=validation.verified)


def export_institution_governance_proof(
    network: InstitutionNetwork | Mapping[str, Any],
    output_dir: str | Path,
    report: InstitutionGovernanceReport | Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    actual = _coerce_report(report, normalized)
    proof = build_institution_governance_proof(normalized, actual)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "institution_governance_state.json"
    proof_path = target / "institution_governance_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_institution_invariant_report(
    network: InstitutionNetwork | Mapping[str, Any],
    output_dir: str | Path,
    report: InstitutionGovernanceReport | Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    normalized = network if isinstance(network, InstitutionNetwork) else InstitutionNetwork.from_mapping(network)
    actual = _coerce_report(report, normalized)
    invariant_report = evaluate_institution_invariants(normalized, actual)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    invariant_path = target / "institution_invariant_report.json"
    invariant_path.write_text(
        json.dumps(invariant_report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"report": invariant_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_institution_governance":
        return build_institution_governance
    raise AttributeError(name)


def _coerce_report(
    report: InstitutionGovernanceReport | Mapping[str, Any] | None,
    network: InstitutionNetwork,
) -> InstitutionGovernanceReport:
    if report is None:
        return build_institution_governance(network)
    if isinstance(report, InstitutionGovernanceReport):
        return report
    if not isinstance(report, Mapping):
        raise InstitutionGovernanceError("report must be a mapping or InstitutionGovernanceReport")
    participant_bindings = tuple((entry["participant_id"], _freeze_value(entry["details"])) for entry in report.get("participant_bindings", ()))
    fleet_bindings = tuple((entry["fleet_id"], _freeze_value(entry["details"])) for entry in report.get("fleet_bindings", ()))
    evidence = report.get("evidence", {})
    if isinstance(evidence, Mapping):
        evidence_items = tuple(sorted((str(key), _freeze_value(val)) for key, val in evidence.items()))
    else:
        evidence_items = tuple(sorted((str(key), _freeze_value(val)) for key, val in evidence))
    return InstitutionGovernanceReport(
        institution_id=_require_text(report.get("institution_id"), "institution_id"),
        domain_type=_require_text(report.get("domain_type"), "domain_type"),
        governance_hash=_require_text(report.get("governance_hash"), "governance_hash"),
        reference_hash=_require_text(report.get("reference_hash"), "reference_hash"),
        policy_hash=_require_text(report.get("policy_hash"), "policy_hash"),
        dispatch_projection=tuple(report.get("dispatch_projection", ())),  # type: ignore[arg-type]
        access_projection=tuple(report.get("access_projection", ())),  # type: ignore[arg-type]
        market_projection=tuple(report.get("market_projection", ())),  # type: ignore[arg-type]
        custody_projection=tuple(report.get("custody_projection", ())),  # type: ignore[arg-type]
        participant_bindings=participant_bindings,
        fleet_bindings=fleet_bindings,
        evidence=evidence_items,
        authority_boundary=_require_text(report.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
    )


def _institution_proof_payload(
    network: InstitutionNetwork,
    report: InstitutionGovernanceReport,
    *,
    verified: bool,
) -> dict[str, Any]:
    proof = {
        "schema": "afritech.mobility.institution_governance_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "institution_id": network.institution_id,
        "domain_type": network.domain_type,
        "reference_hash": network.reference_hash,
        "governance_hash": network.governance_hash,
        "participant_hashes": [participant.participant_hash() for participant in network.participants],
        "fleet_hashes": [fleet.fleet_hash for fleet in network.fleets],
        "policy_types": [policy.policy_type for policy in network.policies],
        "verified": verified,
    }
    proof["proof_hash"] = _canonical_hash(
        {
            key: value
            for key, value in proof.items()
            if key not in {"proof_hash", "governance_hash"}
        }
    )
    return proof


def _policy_projection_for_type(network: InstitutionNetwork, policy_type: str) -> tuple[str, ...]:
    return tuple(sorted(policy.policy_id for policy in network.policies if policy.policy_type == policy_type))


def _dispatch_projection(network: InstitutionNetwork) -> tuple[str, ...]:
    drivers = [participant for participant in network.participants if "driver" in participant.roles]
    others = [participant for participant in network.participants if "driver" not in participant.roles]
    if any(_policy_truthy(policy, "emergency") for policy in network.policies if policy.policy_type == "dispatch"):
        ordered = sorted(drivers, key=lambda participant: (-participant.trust_score, participant.participant_id)) + sorted(others, key=lambda participant: (-participant.trust_score, participant.participant_id))
    else:
        ordered = sorted(network.participants, key=lambda participant: (-participant.trust_score, participant.participant_id))
    return tuple(participant.participant_id for participant in ordered)


def _access_projection(network: InstitutionNetwork) -> tuple[str, ...]:
    values = []
    for policy in network.policies:
        if policy.policy_type == "access":
            values.append(policy.policy_id)
            values.extend(f"{key}={_freeze_value(val)}" for key, val in policy.constraints)
    return tuple(sorted(set(values)))


def _market_projection(network: InstitutionNetwork) -> tuple[str, ...]:
    values = []
    for policy in network.policies:
        if policy.policy_type == "market":
            values.append(policy.policy_id)
            values.extend(f"{key}={_freeze_value(val)}" for key, val in policy.constraints)
    return tuple(sorted(set(values)))


def _custody_projection(network: InstitutionNetwork) -> tuple[str, ...]:
    values = []
    for policy in network.policies:
        if policy.policy_type == "custody":
            values.append(policy.policy_id)
            values.extend(f"{key}={_freeze_value(val)}" for key, val in policy.constraints)
    return tuple(sorted(set(values)))


def _policy_truthy(policy: InstitutionPolicy, key: str) -> bool:
    for constraint_key, constraint_value in policy.constraints:
        if constraint_key == key:
            return bool(constraint_value)
    return False


def _participant_binding_details(participant: MobilityParticipant, network: InstitutionNetwork) -> dict[str, Any]:
    _validate_institution_metadata(participant.metadata, network.institution_id, "participant")
    if participant.verification_status != "verified":
        raise InstitutionGovernanceError("participants must be verified")
    return {
        "participant_hash": participant.participant_hash(),
        "roles": list(participant.roles),
        "trust_score": round(participant.trust_score, 6),
        "verified": participant.verification_status == "verified",
    }


def _fleet_binding_details(fleet: FleetGovernanceReport, network: InstitutionNetwork) -> dict[str, Any]:
    _validate_institution_metadata(fleet, network.institution_id, "fleet")
    if not fleet.verified:
        raise InstitutionGovernanceError("fleets must be verified")
    return {
        "fleet_hash": fleet.fleet_hash,
        "fleet_trust_score": round(fleet.fleet_trust_score, 6),
        "eligible_vehicle_ids": list(fleet.eligible_vehicle_ids),
        "verified": fleet.verified,
    }


def _validate_institution_metadata(value: Any, institution_id: str, label: str) -> None:
    metadata = {}
    if hasattr(value, "metadata"):
        metadata = dict(value.metadata)
    elif isinstance(value, Mapping):
        metadata = dict(value.get("metadata", {}))
    existing = metadata.get("institution_id")
    if existing is not None and existing != institution_id:
        raise InstitutionGovernanceError(f"{label} institution_id mismatch")


def _validate_membership_constraints(network: InstitutionNetwork) -> None:
    participant_ids = [participant.participant_id for participant in network.participants]
    fleet_ids = [fleet.fleet_id for fleet in network.fleets]
    policy_ids = [policy.policy_id for policy in network.policies]
    if len(set(participant_ids)) != len(participant_ids):
        raise InstitutionGovernanceError("duplicate participant identity detected")
    if len(set(fleet_ids)) != len(fleet_ids):
        raise InstitutionGovernanceError("duplicate fleet binding detected")
    if len(set(policy_ids)) != len(policy_ids):
        raise InstitutionGovernanceError("duplicate policy binding detected")
    if not all(policy.policy_id for policy in network.policies):
        raise InstitutionGovernanceError("policies must be explicit")
    if not all(len(policy.policy_hash) == 64 for policy in network.policies):
        raise InstitutionGovernanceError("policies must be hashable")


def _validate_shadow_fields(payload: Mapping[str, Any], network: InstitutionNetwork) -> None:
    if "participant_ids" in payload and list(payload.get("participant_ids", ())) != [participant.participant_id for participant in network.participants]:
        raise InstitutionGovernanceError("participant_ids shadow field mismatch")
    if "participant_hashes" in payload and list(payload.get("participant_hashes", ())) != [participant.participant_hash() for participant in network.participants]:
        raise InstitutionGovernanceError("participant_hashes shadow field mismatch")
    if "fleet_ids" in payload and list(payload.get("fleet_ids", ())) != [fleet.fleet_id for fleet in network.fleets]:
        raise InstitutionGovernanceError("fleet_ids shadow field mismatch")
    if "fleet_hashes" in payload and list(payload.get("fleet_hashes", ())) != [fleet.fleet_hash for fleet in network.fleets]:
        raise InstitutionGovernanceError("fleet_hashes shadow field mismatch")


def _check_policies_hashable(network: InstitutionNetwork) -> InstitutionInvariantCheck:
    satisfied = all(len(policy.policy_hash) == 64 for policy in network.policies) and all(policy.policy_id for policy in network.policies)
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-001",
        satisfied=satisfied,
        details="institutional rules are explicit and hashable",
        evidence_hash=network.governance_hash,
    )


def _check_policies_replayable(network: InstitutionNetwork, actual: InstitutionGovernanceReport, expected: InstitutionGovernanceReport) -> InstitutionInvariantCheck:
    round_tripped = InstitutionNetwork.from_mapping(network.canonical_dict())
    satisfied = actual.canonical_dict() == expected.canonical_dict() and round_tripped.canonical_dict() == network.canonical_dict()
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-002",
        satisfied=satisfied,
        details="institutional policies are replayable",
        evidence_hash=network.reference_hash,
    )


def _check_no_proof_override(network: InstitutionNetwork, report: InstitutionGovernanceReport) -> InstitutionInvariantCheck:
    proof = _institution_proof_payload(network, report, verified=report.verified)
    satisfied = (
        network.authority_boundary == AUTHORITY_BOUNDARY
        and report.authority_boundary == AUTHORITY_BOUNDARY
        and proof["authority_boundary"] == PROOF_AUTHORITY_BOUNDARY
        and len(proof["proof_hash"]) == 64
    )
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-003",
        satisfied=satisfied,
        details="institutions do not override proof authority",
        evidence_hash=report.report_hash(),
    )


def _check_dispatch_constraints_deterministic(network: InstitutionNetwork, report: InstitutionGovernanceReport) -> InstitutionInvariantCheck:
    satisfied = report.dispatch_projection == _dispatch_projection(network)
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-004",
        satisfied=satisfied,
        details="institution dispatch constraints remain deterministic",
        evidence_hash=report.report_hash(),
    )


def _check_boundaries_enforceable(network: InstitutionNetwork, report: InstitutionGovernanceReport) -> InstitutionInvariantCheck:
    satisfied = (
        network.authority_boundary == AUTHORITY_BOUNDARY
        and report.authority_boundary == AUTHORITY_BOUNDARY
        and set(report.dispatch_projection).issubset({participant.participant_id for participant in network.participants})
        and set(report.participant_bindings[i][0] for i in range(len(report.participant_bindings))) == {participant.participant_id for participant in network.participants}
    )
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-005",
        satisfied=satisfied,
        details="institution boundaries are enforceable",
        evidence_hash=network.governance_hash,
    )


def _check_unique_identities(network: InstitutionNetwork) -> InstitutionInvariantCheck:
    participant_ids = [participant.participant_id for participant in network.participants]
    fleet_ids = [fleet.fleet_id for fleet in network.fleets]
    satisfied = len(set(participant_ids)) == len(participant_ids) and len(set(fleet_ids)) == len(fleet_ids)
    return InstitutionInvariantCheck(
        identifier="IA-INSTITUTION-006",
        satisfied=satisfied,
        details="institution networks do not duplicate identities",
        evidence_hash=network.reference_hash,
    )


def _fleet_report_from_mapping(payload: Mapping[str, Any]) -> FleetGovernanceReport:
    if not isinstance(payload, Mapping):
        raise InstitutionGovernanceError("fleet payload must be a mapping")
    required = ("fleet_id", "region_id", "fleet_hash", "operator_id", "operator_hash")
    if any(key not in payload for key in required):
        raise InstitutionGovernanceError("fleet payload missing governance fields")
    return FleetGovernanceReport(
        fleet_id=_require_text(payload.get("fleet_id"), "fleet_id"),
        region_id=_require_text(payload.get("region_id"), "region_id"),
        fleet_hash=_require_hash(payload.get("fleet_hash"), "fleet_hash"),
        operator_id=_require_text(payload.get("operator_id"), "operator_id"),
        operator_hash=_require_hash(payload.get("operator_hash"), "operator_hash"),
        fleet_trust_score=float(payload.get("fleet_trust_score", 0.0)),
        vehicle_health_score=float(payload.get("vehicle_health_score", 0.0)),
        maintenance_score=float(payload.get("maintenance_score", 0.0)),
        eligible_vehicle_ids=tuple(payload.get("eligible_vehicle_ids", ())),  # type: ignore[arg-type]
        vehicle_reports=tuple(
            (entry["vehicle_id"], entry["details"])
            for entry in payload.get("vehicle_reports", ())
        ),
        evidence=tuple(sorted((str(k), _freeze_value(v)) for k, v in payload.get("evidence", {}).items())),
        authority_boundary=_require_text(payload.get("authority_boundary", FLEET_AUTHORITY_BOUNDARY), "authority_boundary"),
    )


__all__ = [
    "ALLOWED_DOMAIN_TYPES",
    "ALLOWED_POLICY_TYPES",
    "AUTHORITY_BOUNDARY",
    "INSTITUTION_POLICY_TYPES",
    "INSTITUTION_PROOF_AUTHORITY_BOUNDARY",
    "INSTITUTION_INVARIANT_IDS",
    "InstitutionGovernanceError",
    "InstitutionGovernanceReport",
    "InstitutionInvariantCheck",
    "InstitutionInvariantReport",
    "InstitutionNetwork",
    "InstitutionPolicy",
    "InstitutionValidationReport",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_institution_governance",
    "build_institution_governance_proof",
    "evaluate_institution_invariants",
    "export_institution_governance_proof",
    "export_institution_invariant_report",
    "validate_institution_governance",
    "validate_institution_invariants",
]
