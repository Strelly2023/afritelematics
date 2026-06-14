"""Validate pilot dataset simulation and first live deployment scenario."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from afritech.simulation.pilot_dataset import generate_airport_pilot_dataset


ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DOC = ROOT / "docs/operations/AFRITECH_FIRST_LIVE_DEPLOYMENT_SCENARIO.md"

REQUIRED_SCENARIO_TEXT = (
    "Status: FIRST LIVE OPERATION SCENARIO",
    "Classification: GOVERNED AIRPORT PILOT DEPLOYMENT SURFACE",
    "Scenario ID: airport-zone-001",
    "Scenario Type: airport",
    "Zone: airport_pickup_dropoff_zone",
    "Live Money: disabled by default",
    "Field evidence remains non-authoritative.",
    "python -m afritech.ci.afritech_pilot_dataset_simulation_validator",
    "python -m afritech.ci.afritech_field_evidence_runtime_validator",
    "unapproved live-money movement occurs",
    "no authority drift occurs",
)


class AfriTechPilotDatasetSimulationValidationError(RuntimeError):
    """Raised when pilot dataset simulation validation fails."""


@dataclass(frozen=True)
class AfriTechPilotDatasetSimulationReport:
    scenario_id: str
    deployment_type: str
    operation_count: int
    signal_count: int
    dataset_hash: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "dataset_hash": self.dataset_hash,
            "deployment_type": self.deployment_type,
            "operation_count": self.operation_count,
            "scenario_id": self.scenario_id,
            "schema": "afritech.pilot_dataset_simulation_report.v1",
            "signal_count": self.signal_count,
            "verified": self.verified,
        }


def validate() -> AfriTechPilotDatasetSimulationReport:
    dataset = generate_airport_pilot_dataset()
    replay = generate_airport_pilot_dataset()
    if dataset.dataset_hash != replay.dataset_hash:
        raise AfriTechPilotDatasetSimulationValidationError(
            "pilot dataset simulation is not deterministic"
        )
    if dataset.scenario.get("scenario_id") != "airport-zone-001":
        raise AfriTechPilotDatasetSimulationValidationError("scenario id mismatch")
    if dataset.scenario.get("deployment_type") != "airport":
        raise AfriTechPilotDatasetSimulationValidationError("deployment type mismatch")
    if dataset.scenario.get("live_money") != "disabled_by_default":
        raise AfriTechPilotDatasetSimulationValidationError(
            "live money must be disabled by default"
        )
    if any(operation.signal_count != 7 for operation in dataset.operations):
        raise AfriTechPilotDatasetSimulationValidationError(
            "each operation must have seven field signals"
        )
    _validate_scenario_doc()

    report = AfriTechPilotDatasetSimulationReport(
        scenario_id=str(dataset.scenario["scenario_id"]),
        deployment_type=str(dataset.scenario["deployment_type"]),
        operation_count=len(dataset.operations),
        signal_count=sum(operation.signal_count for operation in dataset.operations),
        dataset_hash=dataset.dataset_hash,
        verified=dataset.verified,
    )
    if not report.verified:
        raise AfriTechPilotDatasetSimulationValidationError(
            "pilot dataset simulation report failed"
        )
    return report


def _validate_scenario_doc() -> None:
    if not SCENARIO_DOC.exists():
        raise AfriTechPilotDatasetSimulationValidationError(
            f"missing first live deployment scenario doc: {SCENARIO_DOC.relative_to(ROOT)}"
        )
    text = SCENARIO_DOC.read_text(encoding="utf-8")
    for needle in REQUIRED_SCENARIO_TEXT:
        if needle not in text:
            raise AfriTechPilotDatasetSimulationValidationError(
                f"scenario doc missing required text: {needle}"
            )


def format_summary(report: AfriTechPilotDatasetSimulationReport) -> str:
    return "\n".join(
        (
            "AfriTech pilot dataset simulation validation PASSED",
            f"scenario_id={report.scenario_id} deployment_type={report.deployment_type}",
            f"operations={report.operation_count} signals={report.signal_count}",
            f"dataset_hash={report.dataset_hash}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriTechPilotDatasetSimulationValidationError as exc:
        print(f"AfriTech pilot dataset simulation validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
