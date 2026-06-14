"""Validate the live pilot execution checklist and first operator scenario."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_DOC = ROOT / "docs/operations/AFRITECH_LIVE_PILOT_EXECUTION_CHECKLIST.md"
EC2_TEST_RUN_DOC = ROOT / "docs/operations/AFRITECH_EC2_FIRST_TEST_RUN.md"
OPERATOR_SCENARIO_DOC = ROOT / "docs/operations/AFRITECH_FIRST_OPERATOR_DECISION_SCENARIO.md"

REQUIRED_TEXT = {
    CHECKLIST_DOC: (
        "READY FOR REAL PILOT EXECUTION",
        "Phase 0. Scope Lock",
        "Phase 1. Repo Sync",
        "Phase 2. Build and Start",
        "Phase 3. Health Probe",
        "Phase 4. Pilot Simulation",
        "Phase 5. Reality Ingestion",
        "Phase 6. Reconciliation",
        "Phase 7. Operator Decision",
        "Phase 8. GO / STOP Decision",
        "python -m afritech.ci.afritech_operator_decision_protocol_validator",
        "python -m afritech.ci.afritech_live_pilot_execution_validator",
        "GO only if scope, owners, and rollback path are explicit.",
    ),
    EC2_TEST_RUN_DOC: (
        "READY FOR FIRST REAL TEST RUN",
        "git pull",
        "deploy_production_zero_downtime",
        "run_local_production_probe",
        "operator decision protocol validates",
    ),
    OPERATOR_SCENARIO_DOC: (
        "READY FOR DECISION SIMULATION",
        "Scenario A. GO",
        "Scenario B. STOP",
        "The operator may choose only from the governed vocabulary",
    ),
}


class AfriTechLivePilotExecutionValidationError(RuntimeError):
    """Raised when the live pilot execution artifacts are incomplete."""


@dataclass(frozen=True)
class AfriTechLivePilotExecutionValidationReport:
    checklist_doc: str
    ec2_test_run_doc: str
    operator_scenario_doc: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "checklist_doc": self.checklist_doc,
            "ec2_test_run_doc": self.ec2_test_run_doc,
            "operator_scenario_doc": self.operator_scenario_doc,
            "schema": "afritech.live_pilot_execution_validation_report.v1",
            "verified": self.verified,
        }


def validate() -> AfriTechLivePilotExecutionValidationReport:
    for path, required_text in REQUIRED_TEXT.items():
        if not path.exists():
            raise AfriTechLivePilotExecutionValidationError(
                f"missing required artifact: {path.relative_to(ROOT)}"
            )
        text = path.read_text(encoding="utf-8")
        for needle in required_text:
            if needle not in text:
                raise AfriTechLivePilotExecutionValidationError(
                    f"{path.relative_to(ROOT)} missing required text: {needle}"
                )

    report = AfriTechLivePilotExecutionValidationReport(
        checklist_doc=str(CHECKLIST_DOC.relative_to(ROOT)),
        ec2_test_run_doc=str(EC2_TEST_RUN_DOC.relative_to(ROOT)),
        operator_scenario_doc=str(OPERATOR_SCENARIO_DOC.relative_to(ROOT)),
        verified=True,
    )
    return report


def format_summary(report: AfriTechLivePilotExecutionValidationReport) -> str:
    return "\n".join(
        (
            "AfriTech live pilot execution validation PASSED",
            f"checklist={report.checklist_doc}",
            f"ec2_test_run={report.ec2_test_run_doc}",
            f"operator_scenario={report.operator_scenario_doc}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriTechLivePilotExecutionValidationError as exc:
        print(f"AfriTech live pilot execution validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
