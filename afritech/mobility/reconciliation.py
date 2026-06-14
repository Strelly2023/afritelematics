"""Simulation versus reality reconciliation for pilot operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .field_evidence import FieldEvidenceIngestionResult, validate_field_evidence_ingestion

if TYPE_CHECKING:
    from afritech.simulation.pilot_dataset import PilotDatasetSimulation


SCHEMA = "afritech.mobility.simulation_reality_reconciliation.v1"
AUTHORITY_BOUNDARY = "simulation_reality_reconciliation_read_only"
INVARIANT_AUTHORITY_BOUNDARY = "simulation_reality_reconciliation_invariant_read_only"
VALIDATION_AUTHORITY_BOUNDARY = "simulation_reality_reconciliation_validation_read_only"
PROOF_AUTHORITY_BOUNDARY = "simulation_reality_reconciliation_proof_read_only"

SEVERITY_WEIGHTS = {
    "low": 0.1,
    "medium": 0.25,
    "high": 1.0,
}


class SimulationRealityReconciliationError(ValueError):
    """Raised when reconciliation inputs or outputs are invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SimulationRealityReconciliationError(f"{label} is required")
    return value.strip()


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ReconciliationDelta:
    metric: str
    expected: Any
    observed: Any
    severity: str
    note: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_WEIGHTS:
            raise SimulationRealityReconciliationError("invalid divergence severity")
        object.__setattr__(self, "metric", _require_text(self.metric, "metric"))
        object.__setattr__(self, "note", _require_text(self.note, "note"))

    @property
    def weight(self) -> float:
        return SEVERITY_WEIGHTS[self.severity]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "expected": self.expected,
            "metric": self.metric,
            "note": self.note,
            "observed": self.observed,
            "severity": self.severity,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class SimulationRealityReconciliationReport:
    scenario_id: str
    deployment_type: str
    simulation_dataset_hash: str
    live_dataset_hash: str
    operation_count: int
    matched_operation_count: int
    divergence_count: int
    divergence_score: float
    recommendation: str
    deltas: tuple[ReconciliationDelta, ...] = field(default_factory=tuple)
    authority_boundary: str = AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return (
            self.authority_boundary == AUTHORITY_BOUNDARY
            and bool(self.scenario_id)
            and bool(self.deployment_type)
            and len(self.simulation_dataset_hash) == 64
            and len(self.live_dataset_hash) == 64
            and self.operation_count >= 1
            and self.matched_operation_count >= 0
            and self.divergence_count >= 0
            and 0.0 <= self.divergence_score <= 1.0
            and self.recommendation in {
                "continue",
                "continue_with_monitoring",
                "shadow_more",
                "investigate",
                "stop",
            }
        )

    @property
    def aligned(self) -> bool:
        return self.verified and self.divergence_count == 0 and self.recommendation == "continue"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "deltas": [delta.canonical_dict() for delta in self.deltas],
            "deployment_type": self.deployment_type,
            "divergence_count": self.divergence_count,
            "divergence_score": round(self.divergence_score, 6),
            "live_dataset_hash": self.live_dataset_hash,
            "matched_operation_count": self.matched_operation_count,
            "operation_count": self.operation_count,
            "recommendation": self.recommendation,
            "scenario_id": self.scenario_id,
            "schema": SCHEMA,
            "simulation_dataset_hash": self.simulation_dataset_hash,
            "verified": self.verified,
            "aligned": self.aligned,
        }

    @property
    def reconciliation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def reconcile_simulation_and_reality(
    simulation: PilotDatasetSimulation,
    live_results: tuple[FieldEvidenceIngestionResult, ...] | list[FieldEvidenceIngestionResult],
) -> SimulationRealityReconciliationReport:
    if not hasattr(simulation, "verified") or not hasattr(simulation, "operations") or not hasattr(simulation, "scenario"):
        raise SimulationRealityReconciliationError("simulation must be a PilotDatasetSimulation")
    if not bool(getattr(simulation, "verified")):
        raise SimulationRealityReconciliationError("simulation must be verified")
    if not isinstance(live_results, (list, tuple)) or not live_results:
        raise SimulationRealityReconciliationError("live_results are required")

    normalized_live = tuple(
        result if isinstance(result, FieldEvidenceIngestionResult) else _reject_live_mapping(result)
        for result in live_results
    )
    for result in normalized_live:
        if not validate_field_evidence_ingestion(result):
            raise SimulationRealityReconciliationError("live field evidence result failed validation")

    live_by_operation = {result.collection.operation_id: result for result in normalized_live}
    deltas: list[ReconciliationDelta] = []
    matched_operation_count = 0

    simulation_operations = {operation.operation_id: operation for operation in simulation.operations}
    expected_operations = tuple(sorted(simulation_operations))
    observed_operations = tuple(sorted(live_by_operation))

    if expected_operations != observed_operations:
        missing = sorted(set(expected_operations) - set(observed_operations))
        extra = sorted(set(observed_operations) - set(expected_operations))
        if missing:
            deltas.append(
                ReconciliationDelta(
                    metric="operation_set.missing",
                    expected=expected_operations,
                    observed=observed_operations,
                    severity="high",
                    note="live operations are missing simulation operations",
                )
            )
        if extra:
            deltas.append(
                ReconciliationDelta(
                    metric="operation_set.extra",
                    expected=expected_operations,
                    observed=observed_operations,
                    severity="high",
                    note="live operations include unexpected operations",
                )
            )

    for operation_id, expected in simulation_operations.items():
        observed = live_by_operation.get(operation_id)
        if observed is None:
            continue
        matched_operation_count += 1
        _compare_metric(
            deltas,
            metric=f"{operation_id}.selected_participant_id",
            expected=expected.selected_participant_id,
            observed=observed.collection.selected_participant_id,
            note="participant binding diverged",
        )
        _compare_metric(
            deltas,
            metric=f"{operation_id}.signal_count",
            expected=expected.signal_count,
            observed=len(observed.collection.field_events),
            note="signal count diverged",
        )
        _compare_metric(
            deltas,
            metric=f"{operation_id}.collection_hash",
            expected=expected.collection_hash,
            observed=observed.collection.collection_hash,
            note="collection hash diverged",
        )
        _compare_metric(
            deltas,
            metric=f"{operation_id}.proof_hash",
            expected=expected.proof_hash,
            observed=str(observed.proof["proof_hash"]),
            note="proof hash diverged",
        )
        _compare_metric(
            deltas,
            metric=f"{operation_id}.ingestion_hash",
            expected=expected.ingestion_hash,
            observed=observed.ingestion_hash,
            note="ingestion hash diverged",
        )

    divergence_count = len(deltas)
    divergence_score = _divergence_score(deltas, max_checks=max(1, len(simulation_operations) * 5))
    recommendation = _recommend(divergence_score, divergence_count, matched_operation_count, len(simulation_operations))

    report = SimulationRealityReconciliationReport(
        scenario_id=_require_text(simulation.scenario.get("scenario_id"), "scenario_id"),
        deployment_type=_require_text(simulation.scenario.get("deployment_type"), "deployment_type"),
        simulation_dataset_hash=simulation.dataset_hash,
        live_dataset_hash=_canonical_hash([result.canonical_dict() for result in normalized_live]),
        operation_count=len(simulation.operations),
        matched_operation_count=matched_operation_count,
        divergence_count=divergence_count,
        divergence_score=divergence_score,
        recommendation=recommendation,
        deltas=tuple(deltas),
    )
    if not report.verified:
        raise SimulationRealityReconciliationError("reconciliation report failed structural validation")
    return report


def _compare_metric(
    deltas: list[ReconciliationDelta],
    *,
    metric: str,
    expected: Any,
    observed: Any,
    note: str,
) -> None:
    if expected != observed:
        severity = "high" if metric.endswith(("collection_hash", "proof_hash", "ingestion_hash")) else "medium"
        deltas.append(
            ReconciliationDelta(
                metric=metric,
                expected=expected,
                observed=observed,
                severity=severity,
                note=note,
            )
        )


def _divergence_score(deltas: tuple[ReconciliationDelta, ...] | list[ReconciliationDelta], *, max_checks: int) -> float:
    if max_checks <= 0:
        return 0.0
    score = sum(delta.weight for delta in deltas) / float(max_checks)
    return round(min(1.0, score), 6)


def _recommend(
    divergence_score: float,
    divergence_count: int,
    matched_operation_count: int,
    operation_count: int,
) -> str:
    if divergence_count == 0 and matched_operation_count == operation_count:
        return "continue"
    if divergence_score <= 0.1:
        return "continue_with_monitoring"
    if divergence_score <= 0.25:
        return "shadow_more"
    if divergence_score <= 0.5:
        return "investigate"
    return "stop"


def _reject_live_mapping(value: Any) -> FieldEvidenceIngestionResult:
    raise SimulationRealityReconciliationError(
        "live results must be FieldEvidenceIngestionResult instances"
    )


def validate_reconciliation_report(report: SimulationRealityReconciliationReport) -> bool:
    if not isinstance(report, SimulationRealityReconciliationReport):
        raise SimulationRealityReconciliationError("report must be a SimulationRealityReconciliationReport")
    if report.authority_boundary != AUTHORITY_BOUNDARY:
        raise SimulationRealityReconciliationError("reconciliation authority boundary mismatch")
    if not report.verified:
        raise SimulationRealityReconciliationError("reconciliation report is not verified")
    if len(report.deltas) != report.divergence_count:
        raise SimulationRealityReconciliationError("reconciliation delta count mismatch")
    return True


def export_reconciliation_report(
    output_dir: str | Path,
    report: SimulationRealityReconciliationReport,
) -> dict[str, Path]:
    validate_reconciliation_report(report)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / "simulation_reality_reconciliation.json"
    report_path.write_text(json.dumps(report.canonical_dict(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"report": report_path}


__all__ = [
    "AUTHORITY_BOUNDARY",
    "INVARIANT_AUTHORITY_BOUNDARY",
    "PROOF_AUTHORITY_BOUNDARY",
    "SCHEMA",
    "SimulationRealityReconciliationError",
    "SimulationRealityReconciliationReport",
    "ReconciliationDelta",
    "VALIDATION_AUTHORITY_BOUNDARY",
    "export_reconciliation_report",
    "reconcile_simulation_and_reality",
    "validate_reconciliation_report",
]
