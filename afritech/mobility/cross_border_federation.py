"""Deterministic cross-border federation layer for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .legal_compliance_layer import LegalComplianceRecord


SCHEMA = "afritech.mobility.cross_border_federation.v1"
AUTHORITY_BOUNDARY = "cross_border_federation_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "cross_border_federation_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "cross_border_federation_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "cross_border_federation_proof_read_only"

ALLOWED_BORDER_STATUSES = (
    "PENDING",
    "CLEARED",
    "BLOCKED",
    "REVIEW",
)

INVARIANT_IDS = (
    "IA-BORDER-001",
    "IA-BORDER-002",
    "IA-BORDER-003",
    "IA-BORDER-004",
    "IA-BORDER-005",
    "IA-BORDER-006",
)


class CrossBorderFederationError(ValueError):
    """Raised when cross-border federation payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CrossBorderFederationError(f"{label} is required")
    return value.strip()


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise CrossBorderFederationError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str, *, minimum: float = 0.0, maximum: float = 1.0, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise CrossBorderFederationError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise CrossBorderFederationError(f"{label} must be between {minimum} and {maximum}")
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


def _normalize_transitions(values: Iterable[object]) -> tuple["CrossBorderTransition", ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise CrossBorderFederationError("border_transitions must be iterable")
    transitions = tuple(
        item if isinstance(item, CrossBorderTransition) else CrossBorderTransition.from_mapping(item)
        for item in values
    )
    return tuple(sorted(transitions, key=lambda transition: (transition.timestamp, transition.transition_id)))


def _derive_status(compliance: bool, trust_score: float, transitions: tuple["CrossBorderTransition", ...]) -> str:
    if not compliance:
        return "BLOCKED"
    if not transitions:
        return "PENDING"
    return "CLEARED" if trust_score >= 0.75 else "REVIEW"


@dataclass(frozen=True)
class CrossBorderTransition:
    transition_id: str
    participant_id: str
    from_jurisdiction: str
    to_jurisdiction: str
    evidence_hash: str
    timestamp: int
    verified: bool = True
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_id", _require_text(self.transition_id, "transition_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "from_jurisdiction", _require_text(self.from_jurisdiction, "from_jurisdiction"))
        object.__setattr__(self, "to_jurisdiction", _require_text(self.to_jurisdiction, "to_jurisdiction"))
        if self.from_jurisdiction == self.to_jurisdiction:
            raise CrossBorderFederationError("cross-border transition must cross jurisdictions")
        if not isinstance(self.evidence_hash, str) or len(self.evidence_hash) != 64:
            raise CrossBorderFederationError("evidence_hash must be a 64-character hex digest")
        if not isinstance(self.timestamp, int):
            raise CrossBorderFederationError("timestamp must be an integer")
        object.__setattr__(self, "metadata", tuple(sorted((str(key), _freeze_value(val)) for key, val in dict(self.metadata).items())))
        if not isinstance(self.verified, bool) or not self.verified:
            raise CrossBorderFederationError("border transitions must be verified")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CrossBorderTransition":
        if not isinstance(payload, Mapping):
            raise CrossBorderFederationError("border transition payload must be a mapping")
        return cls(
            transition_id=_require_text(payload.get("transition_id") or payload.get("id"), "transition_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            from_jurisdiction=_require_text(payload.get("from_jurisdiction"), "from_jurisdiction"),
            to_jurisdiction=_require_text(payload.get("to_jurisdiction"), "to_jurisdiction"),
            evidence_hash=_require_text(payload.get("evidence_hash") or payload.get("hash"), "evidence_hash"),
            timestamp=int(payload.get("timestamp", 0)),
            verified=bool(payload.get("verified", True)),
            metadata=tuple(payload.get("metadata", ())),  # type: ignore[arg-type]
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_hash": self.evidence_hash,
            "from_jurisdiction": self.from_jurisdiction,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "timestamp": self.timestamp,
            "to_jurisdiction": self.to_jurisdiction,
            "transition_hash": self.transition_hash,
            "transition_id": self.transition_id,
            "verified": self.verified,
        }

    @property
    def transition_hash(self) -> str:
        return _canonical_hash(self.canonical_dict_without_hash())

    def canonical_dict_without_hash(self) -> dict[str, Any]:
        return {
            "evidence_hash": self.evidence_hash,
            "from_jurisdiction": self.from_jurisdiction,
            "metadata": dict(self.metadata),
            "participant_id": self.participant_id,
            "timestamp": self.timestamp,
            "to_jurisdiction": self.to_jurisdiction,
            "transition_id": self.transition_id,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class CrossBorderFederationRecord:
    federation_id: str
    participant_id: str
    from_jurisdiction: str
    to_jurisdiction: str
    certification_hash: str
    compliance_hash: str
    trust_score: float
    compliance: bool
    border_transitions: tuple[CrossBorderTransition, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY
    federation_status: str | None = None
    verified: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "federation_id", _require_text(self.federation_id, "federation_id"))
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "from_jurisdiction", _require_text(self.from_jurisdiction, "from_jurisdiction"))
        object.__setattr__(self, "to_jurisdiction", _require_text(self.to_jurisdiction, "to_jurisdiction"))
        if self.from_jurisdiction == self.to_jurisdiction:
            raise CrossBorderFederationError("cross-border federation requires different jurisdictions")
        for label, value in (("certification_hash", self.certification_hash), ("compliance_hash", self.compliance_hash)):
            if not isinstance(value, str) or len(value) != 64:
                raise CrossBorderFederationError(f"{label} must be a 64-character hex digest")
        object.__setattr__(self, "trust_score", _require_number(self.trust_score, "trust_score"))
        object.__setattr__(self, "compliance", _require_bool(self.compliance, "compliance"))
        object.__setattr__(self, "border_transitions", _normalize_transitions(self.border_transitions))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise CrossBorderFederationError("cross-border authority boundary mismatch")
        if not isinstance(self.verified, bool) or not self.verified:
            raise CrossBorderFederationError("cross-border federation must be verified")

        derived_status = _derive_status(self.compliance, self.trust_score, self.border_transitions)
        if self.federation_status is None:
            object.__setattr__(self, "federation_status", derived_status)
        else:
            object.__setattr__(self, "federation_status", _require_text(self.federation_status, "federation_status"))
            if self.federation_status != derived_status:
                raise CrossBorderFederationError("federation_status mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CrossBorderFederationRecord":
        if not isinstance(payload, Mapping):
            raise CrossBorderFederationError("cross-border payload must be a mapping")
        return cls(
            federation_id=_require_text(payload.get("federation_id"), "federation_id"),
            participant_id=_require_text(payload.get("participant_id"), "participant_id"),
            from_jurisdiction=_require_text(payload.get("from_jurisdiction"), "from_jurisdiction"),
            to_jurisdiction=_require_text(payload.get("to_jurisdiction"), "to_jurisdiction"),
            certification_hash=_require_text(payload.get("certification_hash"), "certification_hash"),
            compliance_hash=_require_text(payload.get("compliance_hash"), "compliance_hash"),
            trust_score=payload.get("trust_score", 0.0),
            compliance=_require_bool(payload.get("compliance"), "compliance"),
            border_transitions=tuple(payload.get("border_transitions", ())),  # type: ignore[arg-type]
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
            federation_status=payload.get("federation_status"),
            verified=bool(payload.get("verified", True)),
        )

    @property
    def federation_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "certification_hash": self.certification_hash,
            "compliance": self.compliance,
            "compliance_hash": self.compliance_hash,
            "border_transitions": [transition.canonical_dict() for transition in self.border_transitions],
            "federation_id": self.federation_id,
            "federation_status": self.federation_status,
            "from_jurisdiction": self.from_jurisdiction,
            "participant_id": self.participant_id,
            "schema": SCHEMA,
            "to_jurisdiction": self.to_jurisdiction,
            "trust_score": self.trust_score,
            "verified": self.verified,
        }

    def canonical_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["federation_hash"] = self.federation_hash
        return payload


@dataclass(frozen=True)
class CrossBorderInvariantCheck:
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
class CrossBorderInvariantReport:
    federation_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[CrossBorderInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "federation_hash": self.federation_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.cross_border_federation_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class CrossBorderValidationReport:
    federation_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "federation_hash": self.federation_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.cross_border_federation_validation_report.v1",
            "verified": self.verified,
        }


def build_cross_border_federation(
    compliance: LegalComplianceRecord | Mapping[str, Any],
    to_jurisdiction: str,
    trust_score: float,
    border_transitions: Iterable[object] = (),
    *,
    federation_id: str = "federation-001",
    compliance_flag: bool = True,
) -> CrossBorderFederationRecord:
    normalized = compliance if isinstance(compliance, LegalComplianceRecord) else LegalComplianceRecord.from_mapping(compliance)
    return CrossBorderFederationRecord(
        federation_id=federation_id,
        participant_id=normalized.participant_id,
        from_jurisdiction=normalized.jurisdiction,
        to_jurisdiction=to_jurisdiction,
        certification_hash=normalized.certification_hash,
        compliance_hash=normalized.compliance_hash,
        trust_score=trust_score,
        compliance=compliance_flag and normalized.compliance,
        border_transitions=tuple(border_transitions),
    )


def _coerce_federation(value: CrossBorderFederationRecord | Mapping[str, Any]) -> CrossBorderFederationRecord:
    if isinstance(value, CrossBorderFederationRecord):
        return value
    return CrossBorderFederationRecord.from_mapping(value)


def build_cross_border_proof(federation: CrossBorderFederationRecord | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_federation(federation)
    proof = {
        "schema": "afritech.mobility.cross_border_federation_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "federation_hash": normalized.federation_hash,
        "federation_id": normalized.federation_id,
        "participant_id": normalized.participant_id,
        "from_jurisdiction": normalized.from_jurisdiction,
        "to_jurisdiction": normalized.to_jurisdiction,
        "certification_hash": normalized.certification_hash,
        "compliance_hash": normalized.compliance_hash,
        "trust_score": round(float(normalized.trust_score), 6),
        "compliance": normalized.compliance,
        "federation_status": normalized.federation_status,
        "border_transitions": [transition.canonical_dict() for transition in normalized.border_transitions],
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_cross_border_invariants(
    federation: CrossBorderFederationRecord | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> CrossBorderInvariantReport:
    normalized = _coerce_federation(federation)
    actual_proof = proof if proof is not None else build_cross_border_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise CrossBorderFederationError("proof must be a mapping")

    round_tripped = CrossBorderFederationRecord.from_mapping(normalized.canonical_dict())
    observed_transition_ids = {transition.transition_id for transition in normalized.border_transitions}
    checks = (
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-001",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="cross-border federation remains read-only",
            evidence_hash=normalized.federation_hash,
        ),
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-002",
            satisfied=normalized.from_jurisdiction != normalized.to_jurisdiction,
            details="jurisdiction change remains explicit",
            evidence_hash=normalized.federation_hash,
        ),
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-003",
            satisfied=0.0 <= normalized.trust_score <= 1.0 and round_tripped.trust_score == normalized.trust_score,
            details="trust transfer remains bounded",
            evidence_hash=normalized.federation_hash,
        ),
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-004",
            satisfied=len(normalized.certification_hash) == 64 and len(normalized.compliance_hash) == 64,
            details="linked certification and compliance hashes remain explicit",
            evidence_hash=normalized.federation_hash,
        ),
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-005",
            satisfied=len(observed_transition_ids) == len(normalized.border_transitions) and all(transition.verified for transition in normalized.border_transitions),
            details="border transitions remain replayable",
            evidence_hash=normalized.federation_hash,
        ),
        CrossBorderInvariantCheck(
            identifier="IA-BORDER-006",
            satisfied=normalized.federation_hash == normalized.canonical_dict()["federation_hash"] and actual_proof.get("proof_hash") is not None,
            details="cross-border federation hash remains stable",
            evidence_hash=normalized.federation_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "federation_hash": normalized.federation_hash,
            "proof_schema": "afritech.mobility.cross_border_federation_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return CrossBorderInvariantReport(
        federation_hash=normalized.federation_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_cross_border_invariants(report: CrossBorderInvariantReport) -> bool:
    if not isinstance(report, CrossBorderInvariantReport):
        raise CrossBorderFederationError("report must be a CrossBorderInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise CrossBorderFederationError("cross-border invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise CrossBorderFederationError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise CrossBorderFederationError(f"{check.identifier} failed: {check.details}")
    return True


def validate_cross_border_federation(federation: CrossBorderFederationRecord | Mapping[str, Any]) -> bool:
    if isinstance(federation, Mapping):
        payload = dict(federation)
        if "federation_hash" not in payload:
            raise CrossBorderFederationError("federation_hash is required")
        if payload.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY:
            record_payload = dict(payload)
            record_payload["authority_boundary"] = AUTHORITY_BOUNDARY
            normalized = CrossBorderFederationRecord.from_mapping(record_payload)
            if payload.get("federation_hash") != normalized.federation_hash:
                raise CrossBorderFederationError("federation_hash mismatch")
            if payload.get("certification_hash") != normalized.certification_hash:
                raise CrossBorderFederationError("certification_hash mismatch")
            if payload.get("compliance_hash") != normalized.compliance_hash:
                raise CrossBorderFederationError("compliance_hash mismatch")
            proof_payload = build_cross_border_proof(normalized)
            if payload.get("proof_hash") != proof_payload["proof_hash"]:
                raise CrossBorderFederationError("proof_hash mismatch")
        else:
            normalized = CrossBorderFederationRecord.from_mapping(payload)
            if payload.get("federation_hash") != normalized.federation_hash:
                raise CrossBorderFederationError("federation_hash mismatch")
            if "proof_hash" in payload:
                proof_payload = build_cross_border_proof(normalized)
                if payload.get("proof_hash") != proof_payload["proof_hash"]:
                    raise CrossBorderFederationError("proof_hash mismatch")
    else:
        normalized = _coerce_federation(federation)
    proof = build_cross_border_proof(normalized)
    report = evaluate_cross_border_invariants(normalized, proof)
    validate_cross_border_invariants(report)
    return True


def export_cross_border_federation(
    output_dir: str | Path,
    federation: CrossBorderFederationRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_federation(federation)
    proof = build_cross_border_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "cross_border_federation.json"
    proof_path = target / "cross_border_federation_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_cross_border_invariant_report(
    output_dir: str | Path,
    federation: CrossBorderFederationRecord | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_federation(federation)
    proof = build_cross_border_proof(normalized)
    report = evaluate_cross_border_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "cross_border_federation_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_cross_border_federation":
        return build_cross_border_federation
    raise AttributeError(name)


__all__ = [
    "AUTHORITY_BOUNDARY",
    "ALLOWED_BORDER_STATUSES",
    "CrossBorderFederationError",
    "CrossBorderFederationRecord",
    "CrossBorderInvariantCheck",
    "CrossBorderInvariantReport",
    "CrossBorderTransition",
    "CrossBorderValidationReport",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_cross_border_federation",
    "build_cross_border_proof",
    "evaluate_cross_border_invariants",
    "export_cross_border_federation",
    "export_cross_border_invariant_report",
    "validate_cross_border_federation",
    "validate_cross_border_invariants",
]
