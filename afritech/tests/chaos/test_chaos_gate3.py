from __future__ import annotations

from afritech.ci.chaos_stability_validator import validate
from afritech.simulation.chaos_v2 import detect_drift, run_chaos_cycles
from afritech.simulation.chaos_v2.stability_proof import (
    REQUIRED_CYCLE_COUNTS,
    run_chaos_stability_proof,
)


def test_chaos_stability_proof_preserves_all_cycles():
    report = run_chaos_stability_proof()

    assert report.verified is True
    assert tuple(run.cycle_count for run in report.runs) == REQUIRED_CYCLE_COUNTS
    for run in report.runs:
        assert all(cycle.verified for cycle in run.cycles)
        assert not any(cycle.drift.drift_detected for cycle in run.cycles)


def test_chaos_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.cycle_counts == REQUIRED_CYCLE_COUNTS


def test_cycle_count_escalation_has_no_cumulative_drift():
    small = run_chaos_cycles(10)
    larger = run_chaos_cycles(100)

    assert small.verified is True
    assert larger.verified is True
    assert {
        cycle.final_result.convergence.replay_hash for cycle in small.cycles
    } == {small.baseline_hashes["replay_hash"]}
    assert {
        cycle.final_result.convergence.replay_hash for cycle in larger.cycles
    } == {larger.baseline_hashes["replay_hash"]}


def test_drift_analyzer_fails_on_any_hash_difference():
    baseline = {
        "admissibility_hash": "a" * 64,
        "convergence_hash": "b" * 64,
        "identity_resolution_hash": "c" * 64,
        "replay_hash": "d" * 64,
    }
    current = {**baseline, "replay_hash": "e" * 64}

    drift = detect_drift(baseline, current)

    assert drift.drift_detected is True
    assert drift.replay_drift is True
    assert drift.identity_drift is False


def test_identity_persists_across_repeated_recoveries():
    run = run_chaos_cycles(25)

    assert {
        cycle.final_result.convergence.identity_resolution_hash
        for cycle in run.cycles
    } == {run.baseline_hashes["identity_resolution_hash"]}

