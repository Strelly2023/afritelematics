"""Deterministic regulator certification layer for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA = "afritech.mobility.regulator_certification.v1"
AUTHORITY_BOUNDARY = "regulator_certification_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "regulator_certification_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "regulator_certification_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "regulator_certification_proof_read_only"

ALLOWED_CERTIFICATION_STATUSES = (
    "PENDING",
    "CERTIFIED",
    "REJECTED",
    "SUSPENDED",
)

INVARIANT_IDS = (
    "IA-REGULATOR-001",
    "IA-REGULATOR-002",
    "IA-REGULATOR-003",
    "IA-REGULATOR-004",
    "IA-REGULATOR-005",
    "IA-REGULATOR-006",
)


class RegulatorCertificationError(ValueError):
    """Raised when regulator certification payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegulatorCertificationError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise RegulatorCertificationError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise RegulatorCertificationError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise RegulatorCertificationError(f"{label} must be between {minimum} and {maximum}")
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


def _normalize_refs(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise RegulatorCertificationError("evidence_refs must be iterable")
    normalized = tuple(_require_text(value, "evidence_ref") for value in values)
    return tuple(sorted(set(normalized)))


def _derive_status(compliance: bool, trust_score: float) -> str:
    if not compliance:
        return "REJECTED"
    return "CERTIFIED" if trust_score >= 0.85 else "PENDING"


@dataclass(frozen=True)
class RegulatorCertificationRecord:
    participant_id: str
    evidence_hash: str
    trust_score: float
    compliance: bool
    jurisdiction: str = "global"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY
    certification_status: str | None = None
    certified: bool | None = None
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "evidence_hash", _require_text(self.evidence_hash, "evidence_hash"))
        if len(self.evidence_hash) != 64:
            raise RegulatorCertificationError("evidence_hash must be a 64-character hex digest")
        object.__setattr__(self, "trust_score", _require_number(self.trust_score, "trust_score"))
        object.__setattr__(self, "compliance", _require_bool(self.compliance, "compliance"))
        object.__setattr__(self, "jurisdiction", _require_text(self.jurisdiction, "jurisdiction"))
        object.__setattr__(self, "evidence_refs", _normalize_refs(self.evidence_refs))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise RegulatorCertificationError("regulator authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise RegulatorCertificationError("regulator certification must be verified")

        derived_status = _derive_status(self.compliance, self.trust_score)
        if self.certification_status is None:
            object.__setattr__(self, "certification_status", derived_status)
        else:
            object.__setattr__(self, "certification_status", _require_text(self.certification_status, "certification_status"))
            if self.certification_status != derived_status:
                raise RegulatorCertificationError("certification_status mismatch")

        derived_certified = self.certification_status == "CERTIFIED"
        if self.certified is None:
            object.__setattr__(self, "certified", derived_certified)
        else:
            object.__setattr__(self, "certified", _require_bool(self.certified, "certified"))
            if self.certified != derived_certified:
                raise RegulatorCertificationError("certified mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RegulatorCertificationRecord":
        if not isinstance(payload, Mapping):
            raise RegulatorCertificationError("certification payload must be a mapping")
        supplied_hash = payload.get("certification_hash")
        return cls(
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            evidence_hash=_require_text(payload.get("evidence_hash"), "evidence_hash"),
            trust_score=payload.get("trust_score", 0.0),
            compliance=_require_bool(payload.get("compliance"), "compliance"),
            jurisdiction=_require_text(payload.get("jurisdiction", "global"), "jurisdiction"),
            evidence_refs=tuple(payload.get("evidence_refs", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            certification_status=payload.get("certification_status"),
            certified=payload.get("certified"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def certification_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "certification_status": self.certification_status,
            "certified": self.certified,
            "compliance": self.compliance,
            "evidence_hash": self.evidence_hash,
            "evidence_refs": list(self.evidence_refs),
            "jurisdiction": self.jurisdiction,
            "participant_id": self.participant_id,
            "schema": SCHEMA,
            "trust_score": self.trust_score,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["certification_hash"] = self.certification_hash
        return payload


@dataclass(frozen=True)
class RegulatorCertificationInvariantCheck:
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
class RegulatorCertificationInvariantReport:
    certification_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[RegulatorCertificationInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "certification_hash": self.certification_hash,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.regulator_certification_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class RegulatorCertificationValidationReport:
    certification_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "certification_hash": self.certification_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.regulator_certification_validation_report.v1",
            "verified": self.verified,
        }


def build_certification_record(
    participant_id: str,
    evidence_hash: str,
    trust_score: float,
    compliance: bool,
    evidence_refs: Iterable[object] = (),
    jurisdiction: str = "global",
) -> RegulatorCertificationRecord:
    return RegulatorCertificationRecord(
        participant_id=participant_id,
        evidence_hash=evidence_hash,
        trust_score=trust_score,
        compliance=compliance,
        evidence_refs=tuple(evidence_refs),
        jurisdiction=jurisdiction,
    )


def _coerce_certification(value: RegulatorCertificationRecord | Mapping[str, Any]) -> RegulatorCertificationRecord:
    if isinstance(value, RegulatorCertificationRecord):
        return value
    return RegulatorCertificationRecord.from_mapping(value)


def build_certification_proof(certification: RegulatorCertificationRecord | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_certification(certification)
    proof = {
        "schema": "afritech.mobility.regulator_certification_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "certification_hash": normalized.certification_hash,
        "participant_id": normalized.participant_id,
        "evidence_hash": normalized.evidence_hash,
        "trust_score": round(float(normalized.trust_score), 6),
        "compliance": normalized.compliance,
        "jurisdiction": normalized.jurisdiction,
        "certification_status": normalized.certification_status,
        "certified": normalized.certified,
        "evidence_refs": list(normalized.evidence_refs),
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_regulator_invariants(
    certification: RegulatorCertificationRecord | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> RegulatorCertificationInvariantReport:
    normalized = _coerce_certification(certification)
    actual_proof = proof if proof is not None else build_certification_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise RegulatorCertificationError("proof must be a mapping")

    round_tripped = RegulatorCertificationRecord.from_mapping(normalized.canonical_dict())
    checks = (
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="regulator certification remains read-only",
            evidence_hash=normalized.certification_hash,
        ),
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-002",
            satisfied=len(normalized.evidence_hash) == 64 and actual_proof.get("evidence_hash") == normalized.evidence_hash,
            details="evidence hash remains explicit",
            evidence_hash=normalized.certification_hash,
        ),
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-003",
            satisfied=0.0 <= normalized.trust_score <= 1.0 and round_tripped.trust_score == normalized.trust_score,
            details="trust score remains bounded",
            evidence_hash=normalized.certification_hash,
        ),
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-004",
            satisfied=normalized.certification_status == _derive_status(normalized.compliance, normalized.trust_score),
            details="certification status remains derived",
            evidence_hash=normalized.certification_hash,
        ),
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-005",
            satisfied=normalized.certified == (normalized.certification_status == "CERTIFIED"),
            details="certified flag remains derived",
            evidence_hash=normalized.certification_hash,
        ),
        RegulatorCertificationInvariantCheck(
            identifier="IA-REGULATOR-006",
            satisfied=normalized.certification_hash == normalized.canonical_dict()["certification_hash"] and actual_proof.get("proof_hash") is not None,
            details="certification hash remains stable",
            evidence_hash=normalized.certification_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "certification_hash": normalized.certification_hash,
            "proof_schema": "afritech.mobility.regulator_certification_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return RegulatorCertificationInvariantReport(
        certification_hash=normalized.certification_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_regulator_invariants(report: RegulatorCertificationInvariantReport) -> bool:
    if not isinstance(report, RegulatorCertificationInvariantReport):
        raise RegulatorCertificationError("report must be a RegulatorCertificationInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise RegulatorCertificationError("regulator invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise RegulatorCertificationError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise RegulatorCertificationError(f"{check.identifier} failed: {check.details}")
    return True


def validate_regulator_certification(certification: RegulatorCertificationRecord | Mapping[str, Any]) -> bool:
    if isinstance(certification, Mapping):
        payload = dict(certification)
        if "certification_hash" not in payload:
            raise RegulatorCertificationError("certification_hash is required")
        normalized = RegulatorCertificationRecord.from_mapping(payload)
        if payload.get("certification_hash") != normalized.certification_hash:
            raise RegulatorCertificationError("certification_hash mismatch")
        if "proof_hash" in payload:
            proof_payload = build_certification_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise RegulatorCertificationError("proof_hash mismatch")
    else:
        normalized = _coerce_certification(certification)
    proof = build_certification_proof(normalized)
    report = evaluate_regulator_invariants(normalized, proof)
    validate_regulator_invariants(report)
    return True


def export_certification(
    output_dir: str | Path,
    certification: RegulatorCertificationRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_certification(certification)
    proof = build_certification_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "regulator_certification.json"
    proof_path = target / "regulator_certification_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_certification_invariant_report(
    output_dir: str | Path,
    certification: RegulatorCertificationRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_certification(certification)
    proof = build_certification_proof(normalized)
    report = evaluate_regulator_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "regulator_certification_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_regulator_certification":
        return build_certification_record
    raise AttributeError(name)


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "RegulatorCertificationError",
    "RegulatorCertificationInvariantCheck",
    "RegulatorCertificationInvariantReport",
    "RegulatorCertificationRecord",
    "RegulatorCertificationValidationReport",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_certification_proof",
    "build_certification_record",
    "evaluate_regulator_invariants",
    "export_certification",
    "export_certification_invariant_report",
    "validate_regulator_certification",
    "validate_regulator_invariants",
]
