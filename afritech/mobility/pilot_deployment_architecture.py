"""Deterministic pilot deployment architecture for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .real_time_execution_engine import RealTimeExecutionError, RealTimeExecutionRecord


SCHEMA = "afritech.mobility.pilot_deployment.v1"
AUTHORITY_BOUNDARY = "pilot_deployment_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "pilot_deployment_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "pilot_deployment_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "pilot_deployment_proof_read_only"

ALLOWED_DEPLOYMENT_STATUSES = (
    "READY",
    "ACTIVE",
    "PAUSED",
    "COMPLETE",
)

INVARIANT_IDS = (
    "IA-PILOT-001",
    "IA-PILOT-002",
    "IA-PILOT-003",
    "IA-PILOT-004",
    "IA-PILOT-005",
    "IA-PILOT-006",
)


class PilotDeploymentError(ValueError):
    """Raised when pilot deployment payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotDeploymentError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise PilotDeploymentError(f"{label} must be a boolean")
    return value


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
        raise PilotDeploymentError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_regions(values: Iterable[object]) -> tuple["PilotRegion", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise PilotDeploymentError("regions must be iterable")
    regions = tuple(item if isinstance(item, PilotRegion) else PilotRegion.from_mapping(item) for item in values)
    return tuple(sorted(regions, key=lambda region: (region.region_id, region.partition_id)))


def _normalize_tenants(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise PilotDeploymentError("tenants must be iterable")
    normalized = tuple(_require_text(value, "tenant") for value in values)
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class PilotRegion:
    region_id: str
    partition_id: str
    authority_scope: str
    replay_hash: str
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "region_id", _require_text(self.region_id, "region_id"))
        object.__setattr__(self, "partition_id", _require_text(self.partition_id, "partition_id"))
        object.__setattr__(self, "authority_scope", _require_text(self.authority_scope, "authority_scope"))
        if not isinstance(self.replay_hash, str) or len(self.replay_hash) != 64:
            raise PilotDeploymentError("replay_hash must be a 64-character hex digest")
        if not isinstance(self.verified, bool) or not self.verified:
            raise PilotDeploymentError("pilot regions must be verified")
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PilotRegion":
        if not isinstance(payload, Mapping):
            raise PilotDeploymentError("region payload must be a mapping")
        return cls(
            region_id=_require_text(payload.get("region_id"), "region_id"),
            partition_id=_require_text(payload.get("partition_id"), "partition_id"),
            authority_scope=_require_text(payload.get("authority_scope"), "authority_scope"),
            replay_hash=_require_text(payload.get("replay_hash"), "replay_hash"),
            verified=bool(payload.get("verified", True)),
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_scope": self.authority_scope,
            "metadata": dict(self.metadata),
            "partition_id": self.partition_id,
            "region_id": self.region_id,
            "replay_hash": self.replay_hash,
            "verified": self.verified,
        }

    @property
    def region_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class PilotDeploymentPlan:
    pilot_id: str
    dispatch_hash: str
    execution_hash: str
    backend_entrypoint: str
    mobile_surface: str
    dashboard_surface: str
    regions: tuple[PilotRegion, ...] = field(default_factory=tuple)
    tenants: tuple[str, ...] = field(default_factory=tuple)
    deployment_stage: str = "READY"
    readiness_gate: bool = False
    authority_boundary: str = AUTHORITY_BOUNDARY
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "pilot_id", _require_text(self.pilot_id, "pilot_id"))
        for label, value in (("dispatch_hash", self.dispatch_hash), ("execution_hash", self.execution_hash)):
            if not isinstance(value, str) or len(value) != 64:
                raise PilotDeploymentError(f"{label} must be a 64-character hex digest")
        object.__setattr__(self, "backend_entrypoint", _require_text(self.backend_entrypoint, "backend_entrypoint"))
        object.__setattr__(self, "mobile_surface", _require_text(self.mobile_surface, "mobile_surface"))
        object.__setattr__(self, "dashboard_surface", _require_text(self.dashboard_surface, "dashboard_surface"))
        object.__setattr__(self, "regions", _normalize_regions(self.regions))
        object.__setattr__(self, "tenants", _normalize_tenants(self.tenants))
        object.__setattr__(self, "deployment_stage", _require_text(self.deployment_stage, "deployment_stage"))
        if self.deployment_stage not in ALLOWED_DEPLOYMENT_STATUSES:
            raise PilotDeploymentError("unsupported deployment stage")
        object.__setattr__(self, "readiness_gate", _require_bool(self.readiness_gate, "readiness_gate"))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise PilotDeploymentError("pilot deployment authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise PilotDeploymentError("pilot deployment must be verified")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PilotDeploymentPlan":
        if not isinstance(payload, Mapping):
            raise PilotDeploymentError("pilot payload must be a mapping")
        return cls(
            pilot_id=_require_text(payload.get("pilot_id"), "pilot_id"),
            dispatch_hash=_require_text(payload.get("dispatch_hash"), "dispatch_hash"),
            execution_hash=_require_text(payload.get("execution_hash"), "execution_hash"),
            backend_entrypoint=_require_text(payload.get("backend_entrypoint"), "backend_entrypoint"),
            mobile_surface=_require_text(payload.get("mobile_surface"), "mobile_surface"),
            dashboard_surface=_require_text(payload.get("dashboard_surface"), "dashboard_surface"),
            regions=tuple(payload.get("regions", ())),  # type: ignore[arg-type]
            tenants=tuple(payload.get("tenants", ())),  # type: ignore[arg-type]
            deployment_stage=_require_text(payload.get("deployment_stage", "READY"), "deployment_stage"),
            readiness_gate=bool(payload.get("readiness_gate", False)),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def deployment_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "backend_entrypoint": self.backend_entrypoint,
            "dashboard_surface": self.dashboard_surface,
            "deployment_stage": self.deployment_stage,
            "dispatch_hash": self.dispatch_hash,
            "execution_hash": self.execution_hash,
            "mobile_surface": self.mobile_surface,
            "pilot_id": self.pilot_id,
            "readiness_gate": self.readiness_gate,
            "regions": [region.canonical_dict() for region in self.regions],
            "schema": SCHEMA,
            "tenants": list(self.tenants),
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["deployment_hash"] = self.deployment_hash
        return payload


@dataclass(frozen=True)
class PilotDeploymentInvariantCheck:
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
class PilotDeploymentInvariantReport:
    deployment_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[PilotDeploymentInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "deployment_hash": self.deployment_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.pilot_deployment_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class PilotDeploymentValidationReport:
    deployment_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "deployment_hash": self.deployment_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.pilot_deployment_validation_report.v1",
            "verified": self.verified,
        }


def build_pilot_deployment(
    execution: RealTimeExecutionRecord | Mapping[str, Any],
    *,
    pilot_id: str = "pilot-001",
    backend_entrypoint: str = "afriride_system.api.main:app",
    mobile_surface: str = "AfriRideMobile",
    dashboard_surface: str = "dashboard",
    regions: Iterable[object] = (),
    tenants: Iterable[object] = (),
    deployment_stage: str = "READY",
    readiness_gate: bool = True,
) -> PilotDeploymentPlan:
    try:
        normalized_execution = execution if isinstance(execution, RealTimeExecutionRecord) else RealTimeExecutionRecord.from_mapping(execution)
    except RealTimeExecutionError as exc:
        raise PilotDeploymentError(str(exc)) from exc
    if not normalized_execution.verified:
        raise PilotDeploymentError("execution record must be verified")
    return PilotDeploymentPlan(
        pilot_id=pilot_id,
        dispatch_hash=normalized_execution.dispatch_hash,
        execution_hash=normalized_execution.execution_hash,
        backend_entrypoint=backend_entrypoint,
        mobile_surface=mobile_surface,
        dashboard_surface=dashboard_surface,
        regions=tuple(regions),
        tenants=tuple(tenants),
        deployment_stage=deployment_stage,
        readiness_gate=readiness_gate,
    )


def _coerce_deployment(value: PilotDeploymentPlan | Mapping[str, Any]) -> PilotDeploymentPlan:
    if isinstance(value, PilotDeploymentPlan):
        return value
    return PilotDeploymentPlan.from_mapping(value)


def build_pilot_deployment_proof(deployment: PilotDeploymentPlan | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_deployment(deployment)
    proof = {
        "schema": "afritech.mobility.pilot_deployment_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "deployment_hash": normalized.deployment_hash,
        "pilot_id": normalized.pilot_id,
        "dispatch_hash": normalized.dispatch_hash,
        "execution_hash": normalized.execution_hash,
        "backend_entrypoint": normalized.backend_entrypoint,
        "mobile_surface": normalized.mobile_surface,
        "dashboard_surface": normalized.dashboard_surface,
        "deployment_stage": normalized.deployment_stage,
        "readiness_gate": normalized.readiness_gate,
        "regions": [region.canonical_dict() for region in normalized.regions],
        "tenants": list(normalized.tenants),
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_pilot_deployment_invariants(
    deployment: PilotDeploymentPlan | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> PilotDeploymentInvariantReport:
    normalized = _coerce_deployment(deployment)
    actual_proof = proof if proof is not None else build_pilot_deployment_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise PilotDeploymentError("proof must be a mapping")

    round_tripped = PilotDeploymentPlan.from_mapping(normalized.canonical_dict())
    region_ids = {region.region_id for region in normalized.regions}
    checks = (
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="pilot deployment remains read-only",
            evidence_hash=normalized.deployment_hash,
        ),
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-002",
            satisfied=len(normalized.dispatch_hash) == 64 and len(normalized.execution_hash) == 64,
            details="dispatch and execution hashes remain explicit",
            evidence_hash=normalized.deployment_hash,
        ),
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-003",
            satisfied=round_tripped.backend_entrypoint == normalized.backend_entrypoint
            and round_tripped.mobile_surface == normalized.mobile_surface
            and round_tripped.dashboard_surface == normalized.dashboard_surface,
            details="pilot surfaces remain replayable",
            evidence_hash=normalized.deployment_hash,
        ),
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-004",
            satisfied=normalized.deployment_stage in ALLOWED_DEPLOYMENT_STATUSES and normalized.readiness_gate,
            details="deployment stage remains governed",
            evidence_hash=normalized.deployment_hash,
        ),
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-005",
            satisfied=len(region_ids) == len(normalized.regions) and all(region.verified for region in normalized.regions),
            details="regions remain unique and verified",
            evidence_hash=normalized.deployment_hash,
        ),
        PilotDeploymentInvariantCheck(
            identifier="IA-PILOT-006",
            satisfied=normalized.deployment_hash == normalized.canonical_dict()["deployment_hash"] and actual_proof.get("proof_hash") is not None,
            details="deployment hash remains stable",
            evidence_hash=normalized.deployment_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "deployment_hash": normalized.deployment_hash,
            "proof_schema": "afritech.mobility.pilot_deployment_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return PilotDeploymentInvariantReport(
        deployment_hash=normalized.deployment_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_pilot_deployment_invariants(report: PilotDeploymentInvariantReport) -> bool:
    if not isinstance(report, PilotDeploymentInvariantReport):
        raise PilotDeploymentError("report must be a PilotDeploymentInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise PilotDeploymentError("pilot deployment invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise PilotDeploymentError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise PilotDeploymentError(f"{check.identifier} failed: {check.details}")
    return True


def validate_pilot_deployment(deployment: PilotDeploymentPlan | Mapping[str, Any]) -> bool:
    if isinstance(deployment, Mapping):
        payload = dict(deployment)
        if "deployment_hash" not in payload:
            raise PilotDeploymentError("deployment_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            normalized = PilotDeploymentPlan.from_mapping(record_payload)
            if payload.get("deployment_hash") != normalized.deployment_hash:
                raise PilotDeploymentError("deployment_hash mismatch")
            if payload.get("dispatch_hash") != normalized.dispatch_hash:
                raise PilotDeploymentError("dispatch_hash mismatch")
            if payload.get("execution_hash") != normalized.execution_hash:
                raise PilotDeploymentError("execution_hash mismatch")
            proof_payload = build_pilot_deployment_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise PilotDeploymentError("proof_hash mismatch")
        else:
            normalized = PilotDeploymentPlan.from_mapping(payload)
            if payload.get("deployment_hash") != normalized.deployment_hash:
                raise PilotDeploymentError("deployment_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_pilot_deployment_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise PilotDeploymentError("proof_hash mismatch")
    else:
        normalized = _coerce_deployment(deployment)
    proof = build_pilot_deployment_proof(normalized)
    report = evaluate_pilot_deployment_invariants(normalized, proof)
    validate_pilot_deployment_invariants(report)
    return True


def export_pilot_deployment(
    output_dir: str | Path,
    deployment: PilotDeploymentPlan | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_deployment(deployment)
    proof = build_pilot_deployment_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "pilot_deployment.json"
    proof_path = target / "pilot_deployment_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_pilot_deployment_invariant_report(
    output_dir: str | Path,
    deployment: PilotDeploymentPlan | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_deployment(deployment)
    proof = build_pilot_deployment_proof(normalized)
    report = evaluate_pilot_deployment_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "pilot_deployment_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_pilot_deployment":
        return build_pilot_deployment
    raise AttributeError(name)


__all__ = [
    "ALLOWED_DEPLOYMENT_STATUSES",
    "AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PilotDeploymentError",
    "PilotDeploymentInvariantCheck",
    "PilotDeploymentInvariantReport",
    "PilotDeploymentPlan",
    "PilotDeploymentValidationReport",
    "PilotRegion",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_pilot_deployment",
    "build_pilot_deployment_proof",
    "evaluate_pilot_deployment_invariants",
    "export_pilot_deployment",
    "export_pilot_deployment_invariant_report",
    "validate_pilot_deployment",
    "validate_pilot_deployment_invariants",
]
