"""Validate multi-node fault proof for production readiness."""

from __future__ import annotations

from afritech.distributed.testing.multi_node_fault_proof import (
    REQUIRED_FAULT_SCENARIOS,
    MultiNodeFaultProofError,
    MultiNodeFaultProofReport,
    run_multi_node_fault_proof,
)


class MultiNodeFaultValidationError(RuntimeError):
    """Raised when multi-node fault validation fails."""


def validate() -> MultiNodeFaultProofReport:
    try:
        report = run_multi_node_fault_proof()
    except MultiNodeFaultProofError as exc:
        raise MultiNodeFaultValidationError(str(exc)) from exc
    _validate_report(report)
    return report


def _validate_report(report: MultiNodeFaultProofReport) -> None:
    scenarios = tuple(scenario.scenario for scenario in report.scenarios)
    if scenarios != REQUIRED_FAULT_SCENARIOS:
        raise MultiNodeFaultValidationError(
            f"fault scenarios mismatch: expected {REQUIRED_FAULT_SCENARIOS}, got {scenarios}"
        )
    for scenario in report.scenarios:
        if not scenario.fault_detected:
            raise MultiNodeFaultValidationError(
                f"fault not detected: {scenario.scenario}"
            )
        if not scenario.recovered:
            raise MultiNodeFaultValidationError(
                f"fault not recovered: {scenario.scenario}"
            )
        if not scenario.replay_preserved:
            raise MultiNodeFaultValidationError(
                f"replay not preserved: {scenario.scenario}"
            )


def main() -> int:
    try:
        report = validate()
    except MultiNodeFaultValidationError as exc:
        print(f"Multi-node fault validation FAILED: {exc}")
        return 1
    for scenario in report.scenarios:
        print(
            "Multi-node fault scenario PASSED: "
            f"{scenario.scenario} replay_hash={scenario.recovered_replay_hash}"
        )
    print(f"Multi-node fault validation PASSED: report_hash={report.report_hash()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
