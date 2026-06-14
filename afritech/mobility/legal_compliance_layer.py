"""Deterministic legal compliance layer for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .regulator_certification_layer import RegulatorCertificationRecord


SCHEMA = "afritech.mobility.legal_compliance.v1"
AUTHORITY_BOUNDARY = "legal_compliance_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "legal_compliance_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "legal_compliance_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "legal_compliance_proof_read_only"

ALLOWED_COMPLIANCE_STATUSES = (
    "PENDING",
    "COMPLIANT",
    "NON_COMPLIANT",
    "ESCALATED",
)

INVARIANT_IDS = (
    "IA-COMPLIANCE-001",
    "IA-COMPLIANCE-002",
    "IA-COMPLIANCE-003",
    "IA-COMPLIANCE-004",
    "IA-COMPLIANCE-005",
    "IA-COMPLIANCE-006",
)


class LegalComplianceError(ValueError):
    """Raised when legal compliance payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LegalComplianceError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise LegalComplianceError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise LegalComplianceError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise LegalComplianceError(f"{label} must be between {minimum} and {maximum}")
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


def _normalize_requirements(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise LegalComplianceError("requirements must be iterable")
    normalized = tuple(_require_text(value, "requirement") for value in values)
    return tuple(sorted(set(normalized)))


def _derive_status(compliance: bool, requirements: tuple[str, ...]) -> str:
    if not compliance:
        return "NON_COMPLIANT"
    return "COMPLIANT" if requirements else "PENDING"


@dataclass(frozen=True)
class LegalComplianceRecord:
    case_id: str
    participant_id: str
    jurisdiction: str
    certification_hash: str
    evidence_hash: str
    requirements: tuple[str, ...] = field(default_factory=tuple)
    compliance: bool = True
    authority_boundary: str = AUTHORITY_BOUNDARY
    compliance_status: str | None = None
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", _require_text(self.case_id, "case_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "jurisdiction", _require_text(self.jurisdiction, "jurisdiction"))
        if not isinstance(self.certification_hash, str) or len(self.certification_hash) != 64:
            raise LegalComplianceError("certification_hash must be a 64-character hex digest")
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise LegalComplianceError("evidence_hash must be a 64-character hex digest")
        object.__setattr__(self, "requirements", _normalize_requirements(self.requirements))
        object.__setattr__(self, "compliance", _require_bool(self.compliance, "compliance"))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise LegalComplianceError("legal compliance authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise LegalComplianceError("legal compliance must be verified")

        derived_status = _derive_status(self.compliance, self.requirements)
        if self.compliance_status is None:
            object.__setattr__(self, "compliance_status", derived_status)
        else:
            object.__setattr__(self, "compliance_status", _require_text(self.compliance_status, "compliance_status"))
            if self.compliance_status != derived_status:
                raise LegalComplianceError("compliance_status mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LegalComplianceRecord":
        if not isinstance(payload, Mapping):
            raise LegalComplianceError("compliance payload must be a mapping")
        return cls(
            case_id=_require_text(payload.get("case_id"), "case_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            jurisdiction=_require_text(payload.get("jurisdiction"), "jurisdiction"),
            certification_hash=_require_text(payload.get("certification_hash"), "certification_hash"),
            evidence_hash=_require_text(payload.get("evidence_hash"), "evidence_hash"),
            requirements=tuple(payload.get("requirements", ())),  # type: ignore[arg-type]
            compliance=_require_bool(payload.get("compliance"), "compliance"),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            compliance_status=payload.get("compliance_status"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def compliance_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "case_id": self.case_id,
            "certification_hash": self.certification_hash,
            "compliance": self.compliance,
            "compliance_status": self.compliance_status,
            "evidence_hash": self.evidence_hash,
            "jurisdiction": self.jurisdiction,
            "participant_id": self.participant_id,
            "requirements": list(self.requirements),
            "schema": SCHEMA,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["compliance_hash"] = self.compliance_hash
        return payload


@dataclass(frozen=True)
class LegalComplianceInvariantCheck:
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
class LegalComplianceInvariantReport:
    compliance_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[LegalComplianceInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "compliance_hash": self.compliance_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.legal_compliance_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class LegalComplianceValidationReport:
    compliance_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "compliance_hash": self.compliance_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.legal_compliance_validation_report.v1",
            "verified": self.verified,
        }


def build_compliance_record(
    participant_id: str,
    certification_hash: str,
    evidence_hash: str,
    jurisdiction: str,
    requirements: Iterable[object] = (),
    *,
    case_id: str = "case-001",
    compliance: bool = True,
) -> LegalComplianceRecord:
    return LegalComplianceRecord(
        case_id=case_id,
        participant_id=participant_id,
        jurisdiction=jurisdiction,
        certification_hash=certification_hash,
        evidence_hash=evidence_hash,
        requirements=tuple(requirements),
        compliance=compliance,
    )


def _coerce_compliance(value: LegalComplianceRecord | Mapping[str, Any]) -> LegalComplianceRecord:
    if isinstance(value, LegalComplianceRecord):
        return value
    return LegalComplianceRecord.from_mapping(value)


def build_compliance_proof(compliance: LegalComplianceRecord | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_compliance(compliance)
    proof = {
        "schema": "afritech.mobility.legal_compliance_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "case_id": normalized.case_id,
        "compliance_hash": normalized.compliance_hash,
        "participant_id": normalized.participant_id,
        "jurisdiction": normalized.jurisdiction,
        "certification_hash": normalized.certification_hash,
        "evidence_hash": normalized.evidence_hash,
        "requirements": list(normalized.requirements),
        "compliance_status": normalized.compliance_status,
        "compliance": normalized.compliance,
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_compliance_invariants(
    compliance: LegalComplianceRecord | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> LegalComplianceInvariantReport:
    normalized = _coerce_compliance(compliance)
    actual_proof = proof if proof is not None else build_compliance_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise LegalComplianceError("proof must be a mapping")

    round_tripped = LegalComplianceRecord.from_mapping(normalized.canonical_dict())
    checks = (
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="legal compliance remains read-only",
            evidence_hash=normalized.compliance_hash,
        ),
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-002",
            satisfied=isinstance(normalized.jurisdiction, str) and bool(normalized.jurisdiction.strip()),
            details="jurisdiction remains explicit",
            evidence_hash=normalized.compliance_hash,
        ),
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-003",
            satisfied=len(normalized.certification_hash) == 64 and len(normalized.evidence_hash) == 64,
            details="linked certification and evidence hashes remain explicit",
            evidence_hash=normalized.compliance_hash,
        ),
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-004",
            satisfied=normalized.compliance_status == _derive_status(normalized.compliance, normalized.requirements),
            details="compliance status remains derived",
            evidence_hash=normalized.compliance_hash,
        ),
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-005",
            satisfied=round_tripped.compliance == normalized.compliance and round_tripped.requirements == normalized.requirements,
            details="compliance record remains replayable",
            evidence_hash=normalized.compliance_hash,
        ),
        LegalComplianceInvariantCheck(
            identifier="IA-COMPLIANCE-006",
            satisfied=normalized.compliance_hash == normalized.canonical_dict()["compliance_hash"] and actual_proof.get("proof_hash") is not None,
            details="compliance hash remains stable",
            evidence_hash=normalized.compliance_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "compliance_hash": normalized.compliance_hash,
            "proof_schema": "afritech.mobility.legal_compliance_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return LegalComplianceInvariantReport(
        compliance_hash=normalized.compliance_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_compliance_invariants(report: LegalComplianceInvariantReport) -> bool:
    if not isinstance(report, LegalComplianceInvariantReport):
        raise LegalComplianceError("report must be a LegalComplianceInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise LegalComplianceError("legal invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise LegalComplianceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise LegalComplianceError(f"{check.identifier} failed: {check.details}")
    return True


def validate_legal_compliance(compliance: LegalComplianceRecord | Mapping[str, Any]) -> bool:
    if isinstance(compliance, Mapping):
        payload = dict(compliance)
        if "compliance_hash" not in payload:
            raise LegalComplianceError("compliance_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            normalized = LegalComplianceRecord.from_mapping(record_payload)
            proof_payload = build_compliance_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise LegalComplianceError("proof_hash mismatch")
        else:
            normalized = LegalComplianceRecord.from_mapping(payload)
            if payload.get("compliance_hash") != normalized.compliance_hash:
                raise LegalComplianceError("compliance_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_compliance_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise LegalComplianceError("proof_hash mismatch")
    else:
        normalized = _coerce_compliance(compliance)
    proof = build_compliance_proof(normalized)
    report = evaluate_compliance_invariants(normalized, proof)
    validate_compliance_invariants(report)
    return True


def export_legal_compliance(
    output_dir: str | Path,
    compliance: LegalComplianceRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_compliance(compliance)
    proof = build_compliance_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "legal_compliance.json"
    proof_path = target / "legal_compliance_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_legal_compliance_invariant_report(
    output_dir: str | Path,
    compliance: LegalComplianceRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_compliance(compliance)
    proof = build_compliance_proof(normalized)
    report = evaluate_compliance_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "legal_compliance_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_legal_compliance":
        return build_compliance_record
    raise AttributeError(name)


__all__ = [
    "AUTHORITY_BOUNDARY",
    "ALLOWED_COMPLIANCE_STATUSES",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "LegalComplianceError",
    "LegalComplianceInvariantCheck",
    "LegalComplianceInvariantReport",
    "LegalComplianceRecord",
    "LegalComplianceValidationReport",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_compliance_proof",
    "build_compliance_record",
    "evaluate_compliance_invariants",
    "export_legal_compliance",
    "export_legal_compliance_invariant_report",
    "validate_compliance_invariants",
    "validate_legal_compliance",
]
