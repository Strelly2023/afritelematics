"""Validate simulation versus reality reconciliation for ADR-0043."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from afritech.mobility.reconciliation import (
    SimulationRealityReconciliationError,
    reconcile_simulation_and_reality,
    validate_reconciliation_report,
)
from afritech.simulation.pilot_dataset import (
    generate_airport_pilot_dataset,
    generate_airport_pilot_ingestions,
)


ROOT = Path(__file__).resolve().parents[2]
ADR_0043 = ROOT / "afritech/governance/adr/ADR-0043-simulation-reality-reconciliation-layer.yaml"
RULE_063 = ROOT / "afritech/governance/rules/RULE-063-simulation-reality-reconciliation.yaml"
BIND_041 = ROOT / "afritech/governance/bindings/BIND-041-simulation-reality-reconciliation.yaml"
ARCH_DOC = ROOT / "docs/architecture/AFRISIMULATION_REALITY_RECONCILIATION.md"
SCENARIO_DOC = ROOT / "docs/operations/AFRITECH_FIRST_LIVE_DEPLOYMENT_SCENARIO.md"
RUNBOOK = ROOT / "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md"

REQUIRED_TEXT = (
    "Status: ACCEPTED RECONCILIATION BOUNDARY",
    "Classification: NON-AUTHORITATIVE OPERATIONAL FEEDBACK SURFACE",
    "Constitution defines authority.",
    "Deterministic Truth defines truth.",
    "Replay validates truth.",
    "Proof demonstrates truth.",
    "simulation vs live field evidence outputs",
    "Scenario ID: airport-zone-001",
    "shadow mode",
    "reconciliation validates",
    "Phase 7. Simulation Reality Reconciliation",
    "python -m afritech.ci.afritech_reconciliation_validator",
)

DOC_REQUIREMENTS = {
    ADR_0043: (
        "Simulation Reality Reconciliation Layer",
        "simulation_vs_reality_comparison",
        "reconciliation_as_truth_authority",
        "BIND-041-simulation-reality-reconciliation.yaml",
        "RULE-063-simulation-reality-reconciliation.yaml",
    ),
    RULE_063: (
        "Simulation Reality Reconciliation Governance",
        "Reconciliation must remain read-only and reference-only.",
        "reconciliation_overrides_dispatch",
        "afritech/ci/afritech_reconciliation_validator.py",
    ),
    BIND_041: (
        "simulation_reality_reconciliation_module",
        "pilot_dataset_simulation_alignment",
        "afritech.ci.afritech_reconciliation_validator",
    ),
    ARCH_DOC: (
        "Status: ACCEPTED RECONCILIATION BOUNDARY",
        "Simulation and reality are compared under this chain. Neither becomes authority.",
        "The reconciliation layer explains divergence only.",
    ),
    SCENARIO_DOC: (
        "Status: FIRST LIVE OPERATION SCENARIO",
        "Shadow Reconciliation",
        "python -m afritech.ci.afritech_reconciliation_validator",
    ),
    RUNBOOK: (
        "Phase 9. Simulation Reality Reconciliation",
        "afritech.ci.afritech_reconciliation_validator",
        "airport-zone-001",
    ),
}


class AfriTechReconciliationValidationError(RuntimeError):
    """Raised when ADR-0043 reconciliation validation fails."""


@dataclass(frozen=True)
class AfriTechReconciliationValidationReport:
    scenario_id: str
    deployment_type: str
    operation_count: int
    divergence_count: int
    divergence_score: float
    recommendation: str
    simulation_dataset_hash: str
    live_dataset_hash: str
    reconciliation_hash: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "deployment_type": self.deployment_type,
            "divergence_count": self.divergence_count,
            "divergence_score": round(self.divergence_score, 6),
            "live_dataset_hash": self.live_dataset_hash,
            "operation_count": self.operation_count,
            "reconciliation_hash": self.reconciliation_hash,
            "recommendation": self.recommendation,
            "scenario_id": self.scenario_id,
            "schema": "afritech.reconciliation_validation_report.v1",
            "simulation_dataset_hash": self.simulation_dataset_hash,
            "verified": self.verified,
        }


def validate() -> AfriTechReconciliationValidationReport:
    simulation = generate_airport_pilot_dataset()
    live_results = generate_airport_pilot_ingestions()
    report = reconcile_simulation_and_reality(simulation, live_results)

    if not validate_reconciliation_report(report):
        raise AfriTechReconciliationValidationError("reconciliation report failed")
    if not report.aligned:
        raise AfriTechReconciliationValidationError("airport reconciliation is not aligned")

    _validate_docs()

    validation_report = AfriTechReconciliationValidationReport(
        scenario_id=report.scenario_id,
        deployment_type=report.deployment_type,
        operation_count=report.operation_count,
        divergence_count=report.divergence_count,
        divergence_score=report.divergence_score,
        recommendation=report.recommendation,
        simulation_dataset_hash=report.simulation_dataset_hash,
        live_dataset_hash=report.live_dataset_hash,
        reconciliation_hash=report.reconciliation_hash,
        verified=report.aligned,
    )
    if not validation_report.verified:
        raise AfriTechReconciliationValidationError(
            "reconciliation validation report failed"
        )
    return validation_report


def _validate_docs() -> None:
    for path, required_text in DOC_REQUIREMENTS.items():
        if not path.exists():
            raise AfriTechReconciliationValidationError(
                f"missing required reconciliation artifact: {path.relative_to(ROOT)}"
            )
        text = path.read_text(encoding="utf-8")
        for needle in required_text:
            if needle not in text:
                raise AfriTechReconciliationValidationError(
                    f"{path.relative_to(ROOT)} missing reconciliation doctrine text: {needle}"
                )


def format_summary(report: AfriTechReconciliationValidationReport) -> str:
    return "\n".join(
        (
            "AfriTech reconciliation validation PASSED",
            f"scenario_id={report.scenario_id} deployment_type={report.deployment_type}",
            f"operations={report.operation_count} divergence_count={report.divergence_count}",
            f"divergence_score={report.divergence_score:.6f} recommendation={report.recommendation}",
            f"reconciliation_hash={report.reconciliation_hash}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except (AfriTechReconciliationValidationError, SimulationRealityReconciliationError) as exc:
        print(f"AfriTech reconciliation validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
