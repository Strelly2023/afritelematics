"""Deterministic public evidence surface for Gen-3 mobility."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA = "afritech.mobility.public_evidence.v1"
AUTHORITY_BOUNDARY = "public_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "public_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "public_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "public_proof_read_only"

INVARIANT_IDS = (
    "IA-PUBLIC-001",
    "IA-PUBLIC-002",
    "IA-PUBLIC-003",
    "IA-PUBLIC-004",
    "IA-PUBLIC-005",
    "IA-PUBLIC-006",
)


class PublicEvidenceError(ValueError):
    """Raised when public evidence payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PublicEvidenceError(f"{label} is required")
    return value.strip()


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise PublicEvidenceError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise PublicEvidenceError(f"{label} must be between {minimum} and {maximum}")
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
        raise PublicEvidenceError("evidence_refs must be iterable")
    normalized = tuple(_require_text(value, "evidence_ref") for value in values)
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class PublicEvidence:
    dispatch_hash: str
    custody_hash: str
    settlement_hash: str
    trust_score: float
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "dispatch_hash", _require_text(self.dispatch_hash, "dispatch_hash"))
        object.__setattr__(self, "custody_hash", _require_text(self.custody_hash, "custody_hash"))
        object.__setattr__(self, "settlement_hash", _require_text(self.settlement_hash, "settlement_hash"))
        if len(self.dispatch_hash) != 64:
            raise PublicEvidenceError("dispatch_hash must be a 64-character hex digest")
        if len(self.custody_hash) != 64:
            raise PublicEvidenceError("custody_hash must be a 64-character hex digest")
        if len(self.settlement_hash) != 64:
            raise PublicEvidenceError("settlement_hash must be a 64-character hex digest")
        object.__setattr__(self, "trust_score", _require_number(self.trust_score, "trust_score"))
        object.__setattr__(self, "evidence_refs", _normalize_refs(self.evidence_refs))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise PublicEvidenceError("public authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise PublicEvidenceError("public evidence must be verified")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PublicEvidence":
        if not isinstance(payload, Mapping):
            raise PublicEvidenceError("public evidence payload must be a mapping")
        if "evidence_hash" in payload:
            supplied_hash = _require_text(payload.get("evidence_hash"), "evidence_hash")
        else:
            supplied_hash = None
        evidence = cls(
            dispatch_hash=_require_text(payload.get("dispatch_hash"), "dispatch_hash"),
            custody_hash=_require_text(payload.get("custody_hash"), "custody_hash"),
            settlement_hash=_require_text(payload.get("settlement_hash"), "settlement_hash"),
            trust_score=float(payload.get("trust_score", 0.0)),
            evidence_refs=tuple(payload.get("evidence_refs", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            verified=bool(payload.get("verified", True)),
        )
        if supplied_hash is not None and supplied_hash != evidence.evidence_hash:
            raise PublicEvidenceError("evidence_hash mismatch")
        return evidence

    @property
    def reference_hash(self) -> str:
        return _canonical_hash(
            {
                "custody_hash": self.custody_hash,
                "dispatch_hash": self.dispatch_hash,
                "settlement_hash": self.settlement_hash,
            }
        )

    @property
    def evidence_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "custody_hash": self.custody_hash,
            "dispatch_hash": self.dispatch_hash,
            "evidence_refs": list(self.evidence_refs),
            "reference_hash": self.reference_hash,
            "settlement_hash": self.settlement_hash,
            "schema": SCHEMA,
            "trust_score": round(float(self.trust_score), 6),
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "custody_hash": self.custody_hash,
            "dispatch_hash": self.dispatch_hash,
            "evidence_hash": self.evidence_hash,
            "evidence_refs": list(self.evidence_refs),
            "reference_hash": self.reference_hash,
            "schema": SCHEMA,
            "settlement_hash": self.settlement_hash,
            "trust_score": round(float(self.trust_score), 6),
            "verified": self.verified,
        }


@dataclass(frozen=True)
class PublicEvidenceInvariantCheck:
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
class PublicEvidenceInvariantReport:
    evidence_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[PublicEvidenceInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "evidence_hash": self.evidence_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.public_evidence_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class PublicEvidenceValidationReport:
    evidence_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "evidence_hash": self.evidence_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.public_evidence_validation_report.v1",
            "verified": self.verified,
        }


def build_public_evidence(
    dispatch_hash: str,
    custody_hash: str,
    settlement_hash: str,
    trust_score: float,
    evidence_refs: Iterable[object] = (),
) -> PublicEvidence:
    return PublicEvidence(
        dispatch_hash=dispatch_hash,
        custody_hash=custody_hash,
        settlement_hash=settlement_hash,
        trust_score=trust_score,
        evidence_refs=tuple(evidence_refs),
    )


def _coerce_evidence(value: PublicEvidence | Mapping[str, Any]) -> PublicEvidence:
    if isinstance(value, PublicEvidence):
        return value
    return PublicEvidence.from_mapping(value)


def build_public_evidence_proof(evidence: PublicEvidence | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_evidence(evidence)
    proof = {
        "schema": "afritech.mobility.public_evidence_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "evidence_hash": normalized.evidence_hash,
        "reference_hash": normalized.reference_hash,
        "dispatch_hash": normalized.dispatch_hash,
        "custody_hash": normalized.custody_hash,
        "settlement_hash": normalized.settlement_hash,
        "trust_score": round(float(normalized.trust_score), 6),
        "evidence_refs": list(normalized.evidence_refs),
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_public_invariants(
    evidence: PublicEvidence | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> PublicEvidenceInvariantReport:
    normalized = _coerce_evidence(evidence)
    actual_proof = proof if proof is not None else build_public_evidence_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise PublicEvidenceError("proof must be a mapping")

    round_tripped = PublicEvidence.from_mapping(normalized.canonical_dict())
    checks = (
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="public evidence remains read-only",
            evidence_hash=normalized.evidence_hash,
        ),
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-002",
            satisfied=isinstance(normalized.dispatch_hash, str),
            details="dispatch hash is explicit",
            evidence_hash=normalized.reference_hash,
        ),
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-003",
            satisfied=isinstance(normalized.custody_hash, str),
            details="custody hash is explicit",
            evidence_hash=normalized.reference_hash,
        ),
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-004",
            satisfied=isinstance(normalized.settlement_hash, str),
            details="settlement hash is explicit",
            evidence_hash=normalized.reference_hash,
        ),
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-005",
            satisfied=0.0 <= normalized.trust_score <= 1.0 and round_tripped.trust_score == normalized.trust_score,
            details="trust score remains bounded",
            evidence_hash=normalized.evidence_hash,
        ),
        PublicEvidenceInvariantCheck(
            identifier="IA-PUBLIC-006",
            satisfied=len(normalized.evidence_hash) == 64 and actual_proof.get("evidence_hash") == normalized.evidence_hash,
            details="public evidence hash remains stable",
            evidence_hash=normalized.evidence_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "evidence_hash": normalized.evidence_hash,
            "proof_schema": "afritech.mobility.public_evidence_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return PublicEvidenceInvariantReport(
        evidence_hash=normalized.evidence_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_public_invariants(report: PublicEvidenceInvariantReport) -> bool:
    if not isinstance(report, PublicEvidenceInvariantReport):
        raise PublicEvidenceError("report must be a PublicEvidenceInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise PublicEvidenceError("public invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise PublicEvidenceError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise PublicEvidenceError(f"{check.identifier} failed: {check.details}")
    return True


def validate_public_evidence(evidence: PublicEvidence | Mapping[str, Any]) -> bool:
    if isinstance(evidence, Mapping):
        payload = dict(evidence)
        if "evidence_hash" not in payload:
            raise PublicEvidenceError("evidence_hash is required")
        if "reference_hash" not in payload:
            raise PublicEvidenceError("reference_hash is required")
        normalized = PublicEvidence.from_mapping(payload)
        if payload.get("evidence_hash") != normalized.evidence_hash:
            raise PublicEvidenceError("evidence_hash mismatch")
        if payload.get("reference_hash") != normalized.reference_hash:
            raise PublicEvidenceError("reference_hash mismatch")
        if "proof_hash" in payload:
            proof_payload = build_public_evidence_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise PublicEvidenceError("proof_hash mismatch")
    else:
        normalized = _coerce_evidence(evidence)
    proof = build_public_evidence_proof(normalized)
    report = evaluate_public_invariants(normalized, proof)
    validate_public_invariants(report)
    return True


def export_public_evidence(
    output_dir: str | Path,
    evidence: PublicEvidence | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_evidence(evidence)
    proof = build_public_evidence_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "public_evidence.json"
    proof_path = target / "public_evidence_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_public_evidence_invariant_report(
    output_dir: str | Path,
    evidence: PublicEvidence | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_evidence(evidence)
    proof = build_public_evidence_proof(normalized)
    report = evaluate_public_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "public_evidence_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_public_evidence":
        return build_public_evidence
    raise AttributeError(name)


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "PublicEvidence",
    "PublicEvidenceError",
    "PublicEvidenceInvariantCheck",
    "PublicEvidenceInvariantReport",
    "PublicEvidenceValidationReport",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_public_evidence",
    "build_public_evidence_proof",
    "evaluate_public_invariants",
    "export_public_evidence",
    "export_public_evidence_invariant_report",
    "validate_public_evidence",
    "validate_public_invariants",
]
