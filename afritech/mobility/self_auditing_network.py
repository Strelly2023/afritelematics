"""Deterministic self-auditing network layer for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA = "afritech.mobility.self_auditing_network.v1"
AUTHORITY_BOUNDARY = "self_auditing_network_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "self_auditing_network_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "self_auditing_network_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "self_auditing_network_proof_read_only"

ALLOWED_AUDIT_STATUSES = (
    "PASS",
    "REVIEW",
    "FAIL",
)

INVARIANT_IDS = (
    "IA-AUDIT-001",
    "IA-AUDIT-002",
    "IA-AUDIT-003",
    "IA-AUDIT-004",
    "IA-AUDIT-005",
    "IA-AUDIT-006",
)


class SelfAuditingNetworkError(ValueError):
    """Raised when self-auditing payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelfAuditingNetworkError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise SelfAuditingNetworkError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise SelfAuditingNetworkError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise SelfAuditingNetworkError(f"{label} must be between {minimum} and {maximum}")
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
        raise SelfAuditingNetworkError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_events(values: Iterable[object]) -> tuple["AuditEvent", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise SelfAuditingNetworkError("audit_events must be iterable")
    events = tuple(item if isinstance(item, AuditEvent) else AuditEvent.from_mapping(item) for item in values)
    return tuple(sorted(events, key=lambda event: (event.timestamp, event.event_id)))


def _derive_status(anomaly_score: float, events: tuple["AuditEvent", ...]) -> str:
    if not events:
        return "FAIL"
    if anomaly_score <= 0.2:
        return "PASS"
    if anomaly_score <= 0.5:
        return "REVIEW"
    return "FAIL"


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: int
    actor: str
    action: str
    evidence_hash: str
    severity: str = "info"
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        if not isinstance(self.timestamp, int):
            raise SelfAuditingNetworkError("timestamp must be an integer")
        object.__setattr__(self, "actor", _require_text(self.actor, "actor"))
        object.__setattr__(self, "action", _require_text(self.action, "action"))
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise SelfAuditingNetworkError("evidence_hash must be a 64-character hex digest")
        object.__setattr__(self, "severity", _require_text(self.severity, "severity"))
        if not isinstance(self.verified, bool) or not self.verified:
            raise SelfAuditingNetworkError("audit events must be verified")
        object.__setattr__(self, "metadata", tuple(sorted((str(key), _freeze_value(val)) for key, val in dict(self.metadata).items())))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AuditEvent":
        if not isinstance(payload, Mapping):
            raise SelfAuditingNetworkError("audit event payload must be a mapping")
        return cls(
            event_id=_require_text(payload.get("event_id") or payload.get("id"), "event_id"),
            timestamp=int(payload.get("timestamp", 0)),
            actor=_require_text(payload.get("actor"), "actor"),
            action=_require_text(payload.get("action"), "action"),
            evidence_hash=_require_text(payload.get("evidence_hash") or payload.get("hash"), "evidence_hash"),
            severity=_require_text(payload.get("severity", "info"), "severity"),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor": self.actor,
            "evidence_hash": self.evidence_hash,
            "event_id": self.event_id,
            "metadata": dict(self.metadata),
            "severity": self.severity,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    @property
    def event_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class SelfAuditingNetworkRecord:
    audit_id: str
    network_id: str
    participant_id: str
    certification_hash: str
    compliance_hash: str
    federation_hash: str
    public_evidence_hash: str
    anomaly_score: float
    audit_events: tuple[AuditEvent, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY
    audit_status: str | None = None
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "audit_id", _require_text(self.audit_id, "audit_id"))
        object.__setattr__(self, "network_id", _require_text(self.network_id, "network_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        for label, value in (
            ("certification_hash", self.certification_hash),
            ("compliance_hash", self.compliance_hash),
            ("federation_hash", self.federation_hash),
            ("public_evidence_hash", self.public_evidence_hash),
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise SelfAuditingNetworkError(f"{label} must be a 64-character hex digest")
        object.__setattr__(self, "anomaly_score", _require_number(self.anomaly_score, "anomaly_score"))
        object.__setattr__(self, "audit_events", _normalize_events(self.audit_events))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise SelfAuditingNetworkError("self-auditing authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise SelfAuditingNetworkError("self-auditing network must be verified")

        derived_status = _derive_status(self.anomaly_score, self.audit_events)
        if self.audit_status is None:
            object.__setattr__(self, "audit_status", derived_status)
        else:
            object.__setattr__(self, "audit_status", _require_text(self.audit_status, "audit_status"))
            if self.audit_status != derived_status:
                raise SelfAuditingNetworkError("audit_status mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SelfAuditingNetworkRecord":
        if not isinstance(payload, Mapping):
            raise SelfAuditingNetworkError("self-auditing payload must be a mapping")
        return cls(
            audit_id=_require_text(payload.get("audit_id"), "audit_id"),
            network_id=_require_text(payload.get("network_id"), "network_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            certification_hash=_require_text(payload.get("certification_hash"), "certification_hash"),
            compliance_hash=_require_text(payload.get("compliance_hash"), "compliance_hash"),
            federation_hash=_require_text(payload.get("federation_hash"), "federation_hash"),
            public_evidence_hash=_require_text(payload.get("public_evidence_hash"), "public_evidence_hash"),
            anomaly_score=payload.get("anomaly_score", 0.0),
            audit_events=tuple(payload.get("audit_events", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            audit_status=payload.get("audit_status"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def audit_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "anomaly_score": self.anomaly_score,
            "audit_events": [event.canonical_dict() for event in self.audit_events],
            "audit_id": self.audit_id,
            "audit_status": self.audit_status,
            "authority_boundary": self.authority_boundary,
            "certification_hash": self.certification_hash,
            "compliance_hash": self.compliance_hash,
            "federation_hash": self.federation_hash,
            "network_id": self.network_id,
            "participant_id": self.participant_id,
            "public_evidence_hash": self.public_evidence_hash,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["audit_hash"] = self.audit_hash
        return payload


@dataclass(frozen=True)
class SelfAuditingInvariantCheck:
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
class SelfAuditingInvariantReport:
    audit_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[SelfAuditingInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "audit_hash": self.audit_hash,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.self_auditing_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class SelfAuditingValidationReport:
    audit_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "audit_hash": self.audit_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.self_auditing_validation_report.v1",
            "verified": self.verified,
        }


def build_self_auditing_network(
    *,
    audit_id: str,
    network_id: str,
    participant_id: str,
    certification_hash: str,
    compliance_hash: str,
    federation_hash: str,
    public_evidence_hash: str,
    anomaly_score: float,
    audit_events: Iterable[object] = (),
) -> SelfAuditingNetworkRecord:
    return SelfAuditingNetworkRecord(
        audit_id=audit_id,
        network_id=network_id,
        participant_id=participant_id,
        certification_hash=certification_hash,
        compliance_hash=compliance_hash,
        federation_hash=federation_hash,
        public_evidence_hash=public_evidence_hash,
        anomaly_score=anomaly_score,
        audit_events=tuple(audit_events),
    )


def _coerce_audit(value: SelfAuditingNetworkRecord | Mapping[str, Any]) -> SelfAuditingNetworkRecord:
    if isinstance(value, SelfAuditingNetworkRecord):
        return value
    return SelfAuditingNetworkRecord.from_mapping(value)


def build_self_audit_proof(audit: SelfAuditingNetworkRecord | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_audit(audit)
    proof = {
        "schema": "afritech.mobility.self_auditing_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "audit_hash": normalized.audit_hash,
        "audit_id": normalized.audit_id,
        "network_id": normalized.network_id,
        "participant_id": normalized.participant_id,
        "certification_hash": normalized.certification_hash,
        "compliance_hash": normalized.compliance_hash,
        "federation_hash": normalized.federation_hash,
        "public_evidence_hash": normalized.public_evidence_hash,
        "anomaly_score": normalized.anomaly_score,
        "audit_status": normalized.audit_status,
        "audit_events": [event.canonical_dict() for event in normalized.audit_events],
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_self_audit_invariants(
    audit: SelfAuditingNetworkRecord | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> SelfAuditingInvariantReport:
    normalized = _coerce_audit(audit)
    actual_proof = proof if proof is not None else build_self_audit_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise SelfAuditingNetworkError("proof must be a mapping")

    round_tripped = SelfAuditingNetworkRecord.from_mapping(normalized.canonical_dict())
    observed_event_ids = {event.event_id for event in normalized.audit_events}
    checks = (
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="self-auditing network remains read-only",
            evidence_hash=normalized.audit_hash,
        ),
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-002",
            satisfied=len(normalized.certification_hash) == 64
            and len(normalized.compliance_hash) == 64
            and len(normalized.federation_hash) == 64
            and len(normalized.public_evidence_hash) == 64,
            details="linked proof hashes remain explicit",
            evidence_hash=normalized.audit_hash,
        ),
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-003",
            satisfied=0.0 <= normalized.anomaly_score <= 1.0 and round_tripped.anomaly_score == normalized.anomaly_score,
            details="anomaly score remains bounded",
            evidence_hash=normalized.audit_hash,
        ),
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-004",
            satisfied=len(observed_event_ids) == len(normalized.audit_events) and all(event.verified for event in normalized.audit_events),
            details="audit events remain replayable",
            evidence_hash=normalized.audit_hash,
        ),
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-005",
            satisfied=normalized.audit_hash == normalized.canonical_dict()["audit_hash"] and actual_proof.get("proof_hash") is not None,
            details="audit hash remains stable",
            evidence_hash=normalized.audit_hash,
        ),
        SelfAuditingInvariantCheck(
            identifier="IA-AUDIT-006",
            satisfied=normalized.audit_status == _derive_status(normalized.anomaly_score, normalized.audit_events),
            details="audit status remains derived",
            evidence_hash=normalized.audit_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "audit_hash": normalized.audit_hash,
            "proof_schema": "afritech.mobility.self_auditing_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return SelfAuditingInvariantReport(
        audit_hash=normalized.audit_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_self_audit_invariants(report: SelfAuditingInvariantReport) -> bool:
    if not isinstance(report, SelfAuditingInvariantReport):
        raise SelfAuditingNetworkError("report must be a SelfAuditingInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise SelfAuditingNetworkError("self-auditing invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise SelfAuditingNetworkError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise SelfAuditingNetworkError(f"{check.identifier} failed: {check.details}")
    return True


def validate_self_auditing_network(audit: SelfAuditingNetworkRecord | Mapping[str, Any]) -> bool:
    if isinstance(audit, Mapping):
        payload = dict(audit)
        if "audit_hash" not in payload:
            raise SelfAuditingNetworkError("audit_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            normalized = SelfAuditingNetworkRecord.from_mapping(record_payload)
            if payload.get("audit_hash") != normalized.audit_hash:
                raise SelfAuditingNetworkError("audit_hash mismatch")
            if payload.get("certification_hash") != normalized.certification_hash:
                raise SelfAuditingNetworkError("certification_hash mismatch")
            if payload.get("compliance_hash") != normalized.compliance_hash:
                raise SelfAuditingNetworkError("compliance_hash mismatch")
            if payload.get("federation_hash") != normalized.federation_hash:
                raise SelfAuditingNetworkError("federation_hash mismatch")
            if payload.get("public_evidence_hash") != normalized.public_evidence_hash:
                raise SelfAuditingNetworkError("public_evidence_hash mismatch")
            proof_payload = build_self_audit_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise SelfAuditingNetworkError("proof_hash mismatch")
        else:
            normalized = SelfAuditingNetworkRecord.from_mapping(payload)
            if payload.get("audit_hash") != normalized.audit_hash:
                raise SelfAuditingNetworkError("audit_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_self_audit_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise SelfAuditingNetworkError("proof_hash mismatch")
    else:
        normalized = _coerce_audit(audit)
    proof = build_self_audit_proof(normalized)
    report = evaluate_self_audit_invariants(normalized, proof)
    validate_self_audit_invariants(report)
    return True


def export_self_auditing_network(
    output_dir: str | Path,
    audit: SelfAuditingNetworkRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_audit(audit)
    proof = build_self_audit_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "self_auditing_network.json"
    proof_path = target / "self_auditing_network_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_self_audit_invariant_report(
    output_dir: str | Path,
    audit: SelfAuditingNetworkRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_audit(audit)
    proof = build_self_audit_proof(normalized)
    report = evaluate_self_audit_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "self_auditing_network_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_self_auditing_network":
        return build_self_auditing_network
    raise AttributeError(name)


__all__ = [
    "AUTHORITY_BOUNDARY",
    "ALLOWED_AUDIT_STATUSES",
    "AuditEvent",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "SelfAuditingInvariantCheck",
    "SelfAuditingInvariantReport",
    "SelfAuditingNetworkError",
    "SelfAuditingNetworkRecord",
    "SelfAuditingValidationReport",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_self_audit_proof",
    "build_self_auditing_network",
    "evaluate_self_audit_invariants",
    "export_self_audit_invariant_report",
    "export_self_auditing_network",
    "validate_self_audit_invariants",
    "validate_self_auditing_network",
]
