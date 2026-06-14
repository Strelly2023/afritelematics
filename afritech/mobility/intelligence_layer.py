"""Deterministic advisory intelligence layer for Gen-3 mobility surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA = "afritech.mobility.intelligence_layer.v1"
AUTHORITY_BOUNDARY = "mobility_intelligence_reference_only"
INVARIANT_AUTHORITY_BOUNDARY = "mobility_intelligence_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "mobility_intelligence_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "mobility_intelligence_proof_read_only"

ALLOWED_INSIGHT_TYPES = ("forecast", "anomaly", "optimization")
INVARIANT_IDS = (
    "IA-INTELLIGENCE-001",
    "IA-INTELLIGENCE-002",
    "IA-INTELLIGENCE-003",
    "IA-INTELLIGENCE-004",
    "IA-INTELLIGENCE-005",
    "IA-INTELLIGENCE-006",
)


class IntelligenceLayerError(ValueError):
    """Raised when advisory intelligence payloads or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntelligenceLayerError(f"{label} is required")
    return value.strip()


def _require_int(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or value < minimum:
        raise IntelligenceLayerError(f"{label} must be an integer >= {minimum}")
    return value


def _require_number(value: object, label: str, *, minimum: float, maximum: float, precision: int = 6) -> float:
    if not isinstance(value, (int, float)):
        raise IntelligenceLayerError(f"{label} must be numeric")
    number = float(value)
    if not minimum <= number <= maximum:
        raise IntelligenceLayerError(f"{label} must be between {minimum} and {maximum}")
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
        raise IntelligenceLayerError("metadata must be a mapping")
    return tuple(sorted((str(key), _freeze_value(val)) for key, val in value.items()))


def _normalize_links(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise IntelligenceLayerError("evidence_links must be iterable")
    normalized = tuple(_require_text(value, "evidence_link") for value in values)
    return tuple(sorted(set(normalized)))


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, round(value, 6)))


def _derive_source_hash(
    insight_type: str,
    region: str,
    demand: int,
    supply: int,
    timestamp: int,
    evidence_links: tuple[str, ...],
    metadata: tuple[tuple[str, Any], ...],
) -> str:
    payload = {
        "demand": demand,
        "evidence_links": list(evidence_links),
        "insight_type": insight_type,
        "metadata": dict(metadata),
        "region": region,
        "supply": supply,
        "timestamp": timestamp,
    }
    return _canonical_hash(payload)


def _derive_confidence(
    insight_type: str,
    demand: int,
    supply: int,
    evidence_links: tuple[str, ...],
) -> float:
    scale = max(demand, supply, 1)
    balance = 1.0 - min(1.0, abs(demand - supply) / float(scale))
    type_factor = {
        "forecast": 0.90,
        "anomaly": 0.82,
        "optimization": 0.94,
    }[insight_type]
    evidence_bonus = min(0.05, len(evidence_links) * 0.01)
    return _clamp(balance * type_factor + evidence_bonus)


def _derive_recommendation(insight_type: str, demand: int, supply: int) -> str:
    if insight_type == "forecast":
        return "monitor_demand_balance" if demand >= supply else "monitor_supply_balance"
    if insight_type == "anomaly":
        return "inspect_operational_variance" if demand <= supply else "inspect_demand_anomaly"
    return "rebalance_supply" if demand > supply else "reduce_idle_capacity"


def _coerce_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IntelligenceLayerError("payload must be a mapping")
    return value


@dataclass(frozen=True)
class MobilityInsight:
    insight_type: str
    region: str
    demand: int
    supply: int
    timestamp: int = 0
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    confidence_score: float | None = None
    recommendation: str | None = None
    source_data_hash: str | None = None
    authority_boundary: str = AUTHORITY_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "insight_type", _require_text(self.insight_type, "insight_type"))
        if self.insight_type not in ALLOWED_INSIGHT_TYPES:
            raise IntelligenceLayerError(f"unsupported insight_type: {self.insight_type}")
        object.__setattr__(self, "region", _require_text(self.region, "region"))
        object.__setattr__(self, "demand", _require_int(self.demand, "demand"))
        object.__setattr__(self, "supply", _require_int(self.supply, "supply"))
        object.__setattr__(self, "timestamp", _require_int(self.timestamp, "timestamp"))
        object.__setattr__(self, "evidence_links", _normalize_links(self.evidence_links))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))
        object.__setattr__(self, "authority_boundary", _require_text(self.authority_boundary, "authority_boundary"))
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise IntelligenceLayerError("intelligence authority boundary mismatch")

        expected_source_hash = _derive_source_hash(
            self.insight_type,
            self.region,
            self.demand,
            self.supply,
            self.timestamp,
            self.evidence_links,
            self.metadata,
        )
        expected_confidence = _derive_confidence(self.insight_type, self.demand, self.supply, self.evidence_links)
        expected_recommendation = _derive_recommendation(self.insight_type, self.demand, self.supply)

        if self.source_data_hash is None:
            object.__setattr__(self, "source_data_hash", expected_source_hash)
        else:
            object.__setattr__(self, "source_data_hash", _require_text(self.source_data_hash, "source_data_hash"))
            if self.source_data_hash != expected_source_hash:
                raise IntelligenceLayerError("source_data_hash mismatch")

        if self.confidence_score is None:
            object.__setattr__(self, "confidence_score", expected_confidence)
        else:
            object.__setattr__(self, "confidence_score", _require_number(self.confidence_score, "confidence_score", minimum=0.0, maximum=1.0))
            if self.confidence_score != expected_confidence:
                raise IntelligenceLayerError("confidence_score mismatch")

        if self.recommendation is None:
            object.__setattr__(self, "recommendation", expected_recommendation)
        else:
            object.__setattr__(self, "recommendation", _require_text(self.recommendation, "recommendation"))
            if self.recommendation != expected_recommendation:
                raise IntelligenceLayerError("recommendation mismatch")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MobilityInsight":
        if not isinstance(payload, Mapping):
            raise IntelligenceLayerError("insight payload must be a mapping")
        return cls(
            insight_type=_require_text(payload.get("insight_type"), "insight_type"),
            region=_require_text(payload.get("region"), "region"),
            demand=int(payload.get("demand", 0)),
            supply=int(payload.get("supply", 0)),
            timestamp=int(payload.get("timestamp", 0)),
            evidence_links=tuple(payload.get("evidence_links", ())),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
            confidence_score=payload.get("confidence_score"),
            recommendation=payload.get("recommendation"),
            source_data_hash=payload.get("source_data_hash"),
            authority_boundary=_require_text(payload.get("authority_boundary", AUTHORITY_BOUNDARY), "authority_boundary"),
        )

    @property
    def is_advisory(self) -> bool:
        return True

    @property
    def insight_hash(self) -> str:
        return _canonical_hash(self._hash_payload())

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and len(self.insight_hash) == 64
            and len(self.source_data_hash or "") == 64
            and 0.0 <= float(self.confidence_score or 0.0) <= 1.0
            and self.is_advisory
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "confidence_score": round(float(self.confidence_score or 0.0), 6),
            "demand": self.demand,
            "evidence_links": list(self.evidence_links),
            "insight_type": self.insight_type,
            "is_advisory": self.is_advisory,
            "metadata": dict(self.metadata),
            "recommendation": self.recommendation,
            "region": self.region,
            "schema": SCHEMA,
            "source_data_hash": self.source_data_hash,
            "supply": self.supply,
            "timestamp": self.timestamp,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "confidence_score": round(float(self.confidence_score or 0.0), 6),
            "demand": self.demand,
            "evidence_links": list(self.evidence_links),
            "insight_hash": self.insight_hash,
            "insight_type": self.insight_type,
            "is_advisory": self.is_advisory,
            "metadata": dict(self.metadata),
            "recommendation": self.recommendation,
            "region": self.region,
            "schema": SCHEMA,
            "source_data_hash": self.source_data_hash,
            "supply": self.supply,
            "timestamp": self.timestamp,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class MobilityInsightInvariantCheck:
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
class MobilityInsightInvariantReport:
    insight_hash: str
    proof_hash: str
    check_hash: str
    checks: tuple[MobilityInsightInvariantCheck, ...]
    authority_boundary: str = INVARIANT_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.authority_boundary == INVARIANT_AUTHORITY_BOUNDARY and all(check.satisfied for check in self.checks)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "check_hash": self.check_hash,
            "checks": [check.canonical_dict() for check in self.checks],
            "insight_hash": self.insight_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.intelligence_invariant_report.v1",
            "verified": self.verified,
        }


@dataclass(frozen=True)
class MobilityInsightValidationReport:
    insight_hash: str
    proof_hash: str
    invariant_report_hash: str
    verified: bool
    authority_boundary: str = VALIDATION_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "insight_hash": self.insight_hash,
            "invariant_report_hash": self.invariant_report_hash,
            "proof_hash": self.proof_hash,
            "schema": "afritech.mobility.intelligence_validation_report.v1",
            "verified": self.verified,
        }


def build_mobility_insight(
    insight_type: str,
    region: str,
    demand: int,
    supply: int,
    *,
    timestamp: int = 0,
    evidence_links: Iterable[object] = (),
    metadata: Mapping[str, Any] | None = None,
) -> MobilityInsight:
    return MobilityInsight(
        insight_type=insight_type,
        region=region,
        demand=demand,
        supply=supply,
        timestamp=timestamp,
        evidence_links=tuple(evidence_links),
        metadata=_freeze_mapping(metadata or {}),
    )


def _coerce_insight(value: MobilityInsight | Mapping[str, Any]) -> MobilityInsight:
    if isinstance(value, MobilityInsight):
        return value
    return MobilityInsight.from_mapping(_coerce_mapping(value))


def build_mobility_insight_proof(insight: MobilityInsight | Mapping[str, Any]) -> dict[str, Any]:
    normalized = _coerce_insight(insight)
    proof = {
        "schema": "afritech.mobility.intelligence_proof.v1",
        "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
        "insight_hash": normalized.insight_hash,
        "insight_type": normalized.insight_type,
        "region": normalized.region,
        "source_data_hash": normalized.source_data_hash,
        "confidence_score": round(float(normalized.confidence_score or 0.0), 6),
        "recommendation": normalized.recommendation,
        "is_advisory": normalized.is_advisory,
        "verified": normalized.verified,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def evaluate_mobility_invariants(
    insight: MobilityInsight | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> MobilityInsightInvariantReport:
    normalized = _coerce_insight(insight)
    actual_proof = proof if proof is not None else build_mobility_insight_proof(normalized)
    if not isinstance(actual_proof, Mapping):
        raise IntelligenceLayerError("proof must be a mapping")

    round_tripped = MobilityInsight.from_mapping(normalized.canonical_dict())
    checks = (
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-001",
            satisfied=normalized.is_advisory,
            details="intelligence remains advisory only",
            evidence_hash=normalized.insight_hash,
        ),
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-002",
            satisfied=normalized.canonical_dict() == round_tripped.canonical_dict(),
            details="intelligence inference is deterministic",
            evidence_hash=normalized.source_data_hash or normalized.insight_hash,
        ),
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-003",
            satisfied=normalized.insight_hash == round_tripped.insight_hash,
            details="intelligence replay is stable",
            evidence_hash=normalized.insight_hash,
        ),
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-004",
            satisfied=normalized.authority_boundary == AUTHORITY_BOUNDARY and actual_proof.get("authority_boundary") == PROOF_AUTHORITY_BOUNDARY,
            details="intelligence does not override authority",
            evidence_hash=normalized.insight_hash,
        ),
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-005",
            satisfied=len(normalized.source_data_hash or "") == 64,
            details="source data hash remains linked",
            evidence_hash=normalized.source_data_hash or normalized.insight_hash,
        ),
        MobilityInsightInvariantCheck(
            identifier="IA-INTELLIGENCE-006",
            satisfied=len(normalized.insight_hash) == 64 and actual_proof.get("insight_hash") == normalized.insight_hash,
            details="insight hash remains stable",
            evidence_hash=normalized.insight_hash,
        ),
    )
    proof_hash = _canonical_hash(
        {
            "authority_boundary": PROOF_AUTHORITY_BOUNDARY,
            "insight_hash": normalized.insight_hash,
            "proof_schema": "afritech.mobility.intelligence_proof.v1",
            "verified": normalized.verified and all(check.satisfied for check in checks),
        }
    )
    return MobilityInsightInvariantReport(
        insight_hash=normalized.insight_hash,
        proof_hash=proof_hash,
        check_hash=_canonical_hash([check.canonical_dict() for check in checks]),
        checks=checks,
    )


def validate_mobility_invariants(report: MobilityInsightInvariantReport) -> bool:
    if not isinstance(report, MobilityInsightInvariantReport):
        raise IntelligenceLayerError("report must be a MobilityInsightInvariantReport")
    if report.authority_boundary != INVARIANT_AUTHORITY_BOUNDARY:
        raise IntelligenceLayerError("intelligence invariant authority boundary mismatch")
    observed = {check.identifier for check in report.checks}
    missing = tuple(identifier for identifier in INVARIANT_IDS if identifier not in observed)
    if missing:
        raise IntelligenceLayerError("missing invariant checks: " + ", ".join(missing))
    for check in report.checks:
        if not check.satisfied:
            raise IntelligenceLayerError(f"{check.identifier} failed: {check.details}")
    return True


def validate_mobility_insight(insight: MobilityInsight | Mapping[str, Any]) -> bool:
    if isinstance(insight, Mapping):
        payload = _coerce_mapping(insight)
        if "insight_hash" not in payload:
            raise IntelligenceLayerError("insight_hash is required")
        normalized = MobilityInsight.from_mapping(payload)
        if payload.get("insight_hash") != normalized.insight_hash:
            raise IntelligenceLayerError("insight_hash mismatch")
    else:
        normalized = _coerce_insight(insight)
    proof = build_mobility_insight_proof(normalized)
    if isinstance(insight, Mapping) and "proof_hash" in insight:
        supplied_proof_hash = _require_text(insight.get("proof_hash"), "proof_hash")
        if supplied_proof_hash != proof["proof_hash"]:
            raise IntelligenceLayerError("proof_hash mismatch")
    report = evaluate_mobility_invariants(normalized, proof)
    validate_mobility_invariants(report)
    return True


def export_mobility_insight(
    output_dir: str | Path,
    insight: MobilityInsight | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_insight(insight)
    proof = build_mobility_insight_proof(normalized)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    state_path = target / "mobility_insight.json"
    proof_path = target / "mobility_insight_proof.json"
    state_path.write_text(json.dumps(normalized.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"json": state_path, "proof": proof_path}


def export_mobility_insight_invariant_report(
    output_dir: str | Path,
    insight: MobilityInsight | Mapping[str, Any],
) -> dict[str, Path]:
    normalized = _coerce_insight(insight)
    proof = build_mobility_insight_proof(normalized)
    report = evaluate_mobility_invariants(normalized, proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "mobility_invariant_report.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


def evaluate_intelligence_invariants(
    insight: MobilityInsight | Mapping[str, Any],
    proof: Mapping[str, Any] | None = None,
) -> MobilityInsightInvariantReport:
    return evaluate_mobility_invariants(insight, proof)


def validate_intelligence_invariants(report: MobilityInsightInvariantReport) -> bool:
    return validate_mobility_invariants(report)


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive aliasing
    if name == "run_mobility_intelligence":
        return build_mobility_insight
    if name == "run_intelligence":
        return build_mobility_insight
    raise AttributeError(name)


__all__ = [
    "ALLOWED_INSIGHT_TYPES",
    "AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "IntelligenceLayerError",
    "MobilityInsight",
    "MobilityInsightInvariantCheck",
    "MobilityInsightInvariantReport",
    "MobilityInsightValidationReport",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "build_mobility_insight",
    "build_mobility_insight_proof",
    "evaluate_intelligence_invariants",
    "evaluate_mobility_invariants",
    "export_mobility_insight",
    "export_mobility_insight_invariant_report",
    "run_intelligence",
    "validate_mobility_insight",
    "validate_intelligence_invariants",
    "validate_mobility_invariants",
]
