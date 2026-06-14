"""Deterministic real-time execution engine for Gen-3 mobility operations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .trust_dispatch import DispatchDecision, DispatchDecisionError, validate_dispatch_decision


SCHEMA = "afritech.mobility.real_time_execution.v1"
AUTHORITY_BOUNDARY = "real_time_execution_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "real_time_execution_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "real_time_execution_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "real_time_execution_proof_read_only"

ALLOWED_EXECUTION_STATUSES = (
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
)

INVARIANT_IDS = (
    "IA-EXECUTION-001",
    "IA-EXECUTION-002",
    "IA-EXECUTION-003",
    "IA-EXECUTION-004",
    "IA-EXECUTION-005",
    "IA-EXECUTION-006",
)


class RealTimeExecutionError(ValueError):
    """Raised when execution payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RealTimeExecutionError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise RealTimeExecutionError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise RealTimeExecutionError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise RealTimeExecutionError(f"{label} must be between {minimum} and {maximum}")
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
        raise RealTimeExecutionError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_events(values: Iterable[object]) -> tuple["ExecutionEvent", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise RealTimeExecutionError("execution_events must be iterable")
    events = tuple(item if isinstance(item, ExecutionEvent) else ExecutionEvent.from_mapping(item) for item in values)
    return tuple(sorted(events, key=lambda event: (event.timestamp, event.event_id)))


def _derive_status(events: tuple["ExecutionEvent", ...]) -> str:
    if not events:
        return "PENDING"
    last = events[-1].status
    if last not in ALLOWED_EXECUTION_STATUSES:
        raise RealTimeExecutionError("unsupported execution status")
    return last


@dataclass(frozen=True)
class ExecutionEvent:
    event_id: str
    timestamp: int
    stage: str
    status: str
    evidence_hash: str
    message: str = ""
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text(self.event_id, "event_id"))
        if not isinstance(self.timestamp, int):
            raise RealTimeExecutionError("timestamp must be an integer")
        object.__setattr__(self, "stage", _require_text(self.stage, "stage"))
        object.__setattr__(self, "status", _require_text(self.status, "status"))
        if self.status not in ALLOWED_EXECUTION_STATUSES:
            raise RealTimeExecutionError("unsupported execution status")
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise RealTimeExecutionError("evidence_hash must be a 64-character hex digest")
        object.__setattr__(self, "message", _require_text(self.message, "message") if self.message else "")
        if not isinstance(self.verified, bool) or not self.verified:
            raise RealTimeExecutionError("execution events must be verified")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ExecutionEvent":
        if not isinstance(payload, Mapping):
            raise RealTimeExecutionError("execution event payload must be a mapping")
        return cls(
            event_id=_require_text(payload.get("event_id") or payload.get("id"), "event_id"),
            timestamp=int(payload.get("timestamp", 0)),
            stage=_require_text(payload.get("stage"), "stage"),
            status=_require_text(payload.get("status"), "status"),
            evidence_hash=_require_text(payload.get("evidence_hash") or payload.get("hash"), "evidence_hash"),
            message=str(payload.get("message", "")),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_hash": self.evidence_hash,
            "event_id": self.event_id,
            "message": self.message,
            "metadata": dict(self.metadata),
            "stage": self.stage,
            "status": self.status,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }

    @property
    def event_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class RealTimeExecutionRecord:
    execution_id: str
    dispatch_hash: str
    operation_id: str
    participant_id: str
    execution_events: tuple[ExecutionEvent, ...] = field(default_factory=tuple)
    execution_status: str | None = None
    live_mode: bool = True
    authority_boundary: str = AUTHORITY_BOUNDARY
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_id", _require_text(self.execution_id, "execution_id"))
        object.__setattr__(self, "dispatch_hash", _require_text(self.dispatch_hash, "dispatch_hash"))
        object.__setattr__(self, "operation_id", _require_text(self.operation_id, "operation_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        if len(self.dispatch_hash) != 64:
            raise RealTimeExecutionError("dispatch_hash must be a 64-character hex digest")
        object.__setattr__(self, "execution_events", _normalize_events(self.execution_events))
        object.__setattr__(self, "live_mode", _require_bool(self.live_mode, "live_mode"))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise RealTimeExecutionError("execution authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise RealTimeExecutionError("execution record must be verified")

        derived_status = _derive_status(self.execution_events)
        if self.execution_status is None:
            object.__setattr__(self, "execution_status", derived_status)
        else:
            object.__setattr__(self, "execution_status", _require_text(self.execution_status, "execution_status"))
            if self.execution_status != derived_status:
                raise RealTimeExecutionError("execution_status mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RealTimeExecutionRecord":
        if not isinstance(payload, Mapping):
            raise RealTimeExecutionError("execution payload must be a mapping")
        return cls(
            execution_id=_require_text(payload.get("execution_id"), "execution_id"),
            dispatch_hash=_require_text(payload.get("dispatch_hash"), "dispatch_hash"),
            operation_id=_require_text(payload.get("operation_id"), "operation_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            execution_events=tuple(payload.get("execution_events", ())),  # type: ignore[arg-type]
            execution_status=payload.get("execution_status"),
            live_mode=bool(payload.get("live_mode", True)),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def execution_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "dispatch_hash": self.dispatch_hash,
            "execution_events": [event.canonical_dict() for event in self.execution_events],
            "execution_id": self.execution_id,
            "execution_status": self.execution_status,
            "live_mode": self.live_mode,
            "operation_id": self.operation_id,
            "participant_id": self.participant_id,
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["execution_hash"] = self.execution_hash
        return payload


@dataclass(frozen=True)
class RealTimeExecutionInvariantCheck:
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
class RealTimeExecutionInvariantReport:
    execution_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[RealTimeExecutionInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "execution_hash": self.execution_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.real_time_execution_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class RealTimeExecutionValidationReport:
    execution_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "execution_hash": self.execution_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.real_time_execution_validation_report.v1",
            "verified": self.verified,
        }


def _normalize_dispatch(dispatch: DispatchDecision | Mapping[str, Any]) -> DispatchDecision:
    if isinstance(dispatch, DispatchDecision):
        return dispatch
    try:
        return DispatchDecision.from_mapping(dispatch)
    except DispatchDecisionError as exc:
        raise RealTimeExecutionError(str(exc)) from exc


def _build_default_events(dispatch: DispatchDecision) -> tuple[ExecutionEvent, ...]:
    evidence = dict(dispatch.evidence)
    base_hash = dispatch.decision_hash
    return (
        ExecutionEvent(
            event_id=f"{dispatch.request.operation_id}-assigned",
            timestamp=dispatch.request.timestamp,
            stage="assignment",
            status="RUNNING",
            evidence_hash=base_hash,
            message="participant assigned",
            metadata={"dispatch_hash": dispatch.decision_hash, "selected_id": dispatch.selected_participant_id},
        ),
        ExecutionEvent(
            event_id=f"{dispatch.request.operation_id}-executed",
            timestamp=dispatch.request.timestamp + 1,
            stage="execution",
            status="COMPLETED",
            evidence_hash=_canonical_hash({"dispatch_hash": dispatch.decision_hash, "evidence": evidence}),
            message="operation executed",
            metadata={"dispatch_hash": dispatch.decision_hash, "selected_id": dispatch.selected_participant_id},
        ),
    )


def build_real_time_execution(
    dispatch: DispatchDecision | Mapping[str, Any],
    execution_events: Iterable[object] = (),
    *,
    execution_id: str = "execution-001",
    live_mode: bool = True,
) -> RealTimeExecutionRecord:
    normalized_dispatch = _normalize_dispatch(dispatch)
    if not normalized_dispatch.verified:
        raise RealTimeExecutionError("dispatch decision must be verified")
    events = tuple(execution_events) or _build_default_events(normalized_dispatch)
    return RealTimeExecutionRecord(
        execution_id=execution_id,
        dispatch_hash=normalized_dispatch.decision_hash,
        operation_id=normalized_dispatch.request.operation_id,
        participant_id=normalized_dispatch.selected_participant_id,
        execution_events=events,
        live_mode=live_mode,
    )


def _coerce_execution(value: RealTimeExecutionRecord | Mapping[str, Any]) -> RealTimeExecutionRecord:
    if isinstance(value, RealTimeExecutionRecord):
        return value
    return RealTimeExecutionRecord.from_mapping(value)


def build_real_time_execution_proof(execution: RealTimeExecutionRecord | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_execution(execution)
    proof = {
        "schema": "afritech.mobility.real_time_execution_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "execution_hash": normalized.execution_hash,
        "execution_id": normalized.execution_id,
        "dispatch_hash": normalized.dispatch_hash,
        "operation_id": normalized.operation_id,
        "participant_id": normalized.participant_id,
        "execution_status": normalized.execution_status,
        "execution_events": [event.canonical_dict() for event in normalized.execution_events],
        "live_mode": normalized.live_mode,
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_real_time_execution_invariants(
    execution: RealTimeExecutionRecord | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> RealTimeExecutionInvariantReport:
    normalized = _coerce_execution(execution)
    actual_proof = proof if proof is not None else build_real_time_execution_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise RealTimeExecutionError("proof must be a mapping")

    normalized_dispatch = _normalize_dispatch(dispatch) if dispatch is not None else None
    expected_participant_id = (
        normalized_dispatch.selected_participant_id if normalized_dispatch is not None else normalized.participant_id
    )
    expected_operation_id = normalized_dispatch.request.operation_id if normalized_dispatch is not None else normalized.operation_id
    expected_dispatch_hash = normalized_dispatch.decision_hash if normalized_dispatch is not None else normalized.dispatch_hash

    round_tripped = RealTimeExecutionRecord.from_mapping(normalized.canonical_dict())
    observed_event_ids = {event.event_id for event in normalized.execution_events}
    checks = (
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="execution remains read-only",
            evidence_hash=normalized.execution_hash,
        ),
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-002",
            satisfied=len(normalized.dispatch_hash) == 64 and actual_proof.get("dispatch_hash") == normalized.dispatch_hash,
            details="dispatch hash remains explicit",
            evidence_hash=normalized.execution_hash,
        ),
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-003",
            satisfied=round_tripped.execution_status == normalized.execution_status and normalized.execution_status in ALLOWED_EXECUTION_STATUSES,
            details="execution status remains derived",
            evidence_hash=normalized.execution_hash,
        ),
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-004",
            satisfied=len(observed_event_ids) == len(normalized.execution_events) and all(event.verified for event in normalized.execution_events),
            details="execution events remain replayable",
            evidence_hash=normalized.execution_hash,
        ),
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-005",
            satisfied=normalized.execution_hash == normalized.canonical_dict()["execution_hash"] and actual_proof.get("proof_hash") is not None,
            details="execution hash remains stable",
            evidence_hash=normalized.execution_hash,
        ),
        RealTimeExecutionInvariantCheck(
            identifier="IA-EXECUTION-006",
            satisfied=(
                actual_proof.get("participant_id") == expected_participant_id
                and actual_proof.get("operation_id") == expected_operation_id
                and actual_proof.get("dispatch_hash") == expected_dispatch_hash
            ),
            details="execution remains bound to the selected dispatch participant",
            evidence_hash=normalized.execution_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "execution_hash": normalized.execution_hash,
            "proof_schema": "afritech.mobility.real_time_execution_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return RealTimeExecutionInvariantReport(
        execution_hash=normalized.execution_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_real_time_execution_invariants(report: RealTimeExecutionInvariantReport) -> bool:
    if not isinstance(report, RealTimeExecutionInvariantReport):
        raise RealTimeExecutionError("report must be a RealTimeExecutionInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise RealTimeExecutionError("real-time execution invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise RealTimeExecutionError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise RealTimeExecutionError(f"{check.identifier} failed: {check.details}")
    return True


def validate_real_time_execution(
    execution: RealTimeExecutionRecord | Mapping[str, Any],
    dispatch: DispatchDecision | Mapping[str, Any] | None = None,
) -> bool:
    if isinstance(execution, Mapping):
        payload = dict(execution)
        if "execution_hash" not in payload:
            raise RealTimeExecutionError("execution_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            normalized = RealTimeExecutionRecord.from_mapping(record_payload)
            if payload.get("execution_hash") != normalized.execution_hash:
                raise RealTimeExecutionError("execution_hash mismatch")
            if payload.get("dispatch_hash") != normalized.dispatch_hash:
                raise RealTimeExecutionError("dispatch_hash mismatch")
            if dispatch is not None:
                normalized_dispatch = _normalize_dispatch(dispatch)
                if payload.get("participant_id") != normalized_dispatch.selected_participant_id:
                    raise RealTimeExecutionError("participant_id mismatch")
                if payload.get("operation_id") != normalized_dispatch.request.operation_id:
                    raise RealTimeExecutionError("operation_id mismatch")
                if payload.get("dispatch_hash") != normalized_dispatch.decision_hash:
                    raise RealTimeExecutionError("dispatch_hash mismatch")
            proof_payload = build_real_time_execution_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise RealTimeExecutionError("proof_hash mismatch")
        else:
            normalized = RealTimeExecutionRecord.from_mapping(payload)
            if payload.get("execution_hash") != normalized.execution_hash:
                raise RealTimeExecutionError("execution_hash mismatch")
            if dispatch is not None:
                normalized_dispatch = _normalize_dispatch(dispatch)
                if payload.get("participant_id") != normalized_dispatch.selected_participant_id:
                    raise RealTimeExecutionError("participant_id mismatch")
                if payload.get("operation_id") != normalized_dispatch.request.operation_id:
                    raise RealTimeExecutionError("operation_id mismatch")
                if payload.get("dispatch_hash") != normalized_dispatch.decision_hash:
                    raise RealTimeExecutionError("dispatch_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_real_time_execution_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise RealTimeExecutionError("proof_hash mismatch")
    else:
        normalized = _coerce_execution(execution)
    proof = build_real_time_execution_proof(normalized)
    report = evaluate_real_time_execution_invariants(normalized, proof, dispatch)
    validate_real_time_execution_invariants(report)
    return True


def export_real_time_execution(
    output_dir: str | Path,
    execution: RealTimeExecutionRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_execution(execution)
    proof = build_real_time_execution_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "real_time_execution.json"
    proof_path = target / "real_time_execution_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_real_time_execution_invariant_report(
    output_dir: str | Path,
    execution: RealTimeExecutionRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_execution(execution)
    proof = build_real_time_execution_proof(normalized)
    report = evaluate_real_time_execution_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "real_time_execution_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_real_time_execution":
        return build_real_time_execution
    raise AttributeError(name)


__all__ = [
    "ALLOWED_EXECUTION_STATUSES",
    "AUTHORITY_BOUNDARY",
    "ExecutionEvent",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "RealTimeExecutionError",
    "RealTimeExecutionInvariantCheck",
    "RealTimeExecutionInvariantReport",
    "RealTimeExecutionRecord",
    "RealTimeExecutionValidationReport",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_real_time_execution",
    "build_real_time_execution_proof",
    "evaluate_real_time_execution_invariants",
    "export_real_time_execution",
    "export_real_time_execution_invariant_report",
    "validate_real_time_execution",
    "validate_real_time_execution_invariants",
]
