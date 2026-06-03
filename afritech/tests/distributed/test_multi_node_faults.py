from __future__ import annotations

import pytest

from afritech.ci.multi_node_fault_validator import _validate_report
from afritech.distributed.testing.multi_node_fault_proof import (
    REQUIRED_FAULT_SCENARIOS,
    MultiNodeFaultProofError,
    MultiNodeFaultProofReport,
    run_multi_node_fault_proof,
)


def test_multi_node_fault_proof_verifies_required_scenarios():
    report = run_multi_node_fault_proof()

    assert report.verified is True
    assert tuple(s.scenario for s in report.scenarios) == REQUIRED_FAULT_SCENARIOS
    assert len(report.report_hash()) == 64


def test_multi_node_fault_scenarios_preserve_replay_after_recovery():
    report = run_multi_node_fault_proof()

    for scenario in report.scenarios:
        assert scenario.fault_detected is True
        assert scenario.recovered is True
        assert scenario.replay_preserved is True
        assert scenario.baseline_replay_hash == scenario.recovered_replay_hash


def test_multi_node_fault_report_rejects_missing_scenario():
    report = run_multi_node_fault_proof()
    broken = MultiNodeFaultProofReport(scenarios=report.scenarios[:-1])

    with pytest.raises(Exception, match="fault scenarios mismatch"):
        _validate_report(broken)


def test_multi_node_fault_proof_rejects_invalid_report():
    report = run_multi_node_fault_proof()
    original = report.scenarios[0]
    broken_scenario = report.scenarios[0].__class__(
        scenario=original.scenario,
        fault_detected=False,
        recovered=original.recovered,
        replay_preserved=original.replay_preserved,
        baseline_replay_hash=original.baseline_replay_hash,
        recovered_replay_hash=original.recovered_replay_hash,
        evidence_hash=original.evidence_hash,
    )
    broken = MultiNodeFaultProofReport(
        scenarios=(broken_scenario, *report.scenarios[1:])
    )

    with pytest.raises(Exception, match="fault not detected"):
        _validate_report(broken)


def test_multi_node_fault_error_type_is_runtime_error():
    assert issubclass(MultiNodeFaultProofError, RuntimeError)
