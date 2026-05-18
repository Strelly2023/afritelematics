from __future__ import annotations

import yaml
from pathlib import Path

from afritech.simulation.adversarial.runner import run_all
from afritech.simulation.adversarial.scenarios import SCENARIOS


INDEX = Path("afritech/simulation/adversarial/index.yaml")


def test_all_indexed_adversarial_scenarios_execute() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    indexed = set(payload["scenarios"])

    assert indexed.issubset(set(SCENARIOS))

    results = run_all(sorted(indexed))

    assert len(results) == len(indexed)
    assert all(result.accepted for result in results)


def test_adversarial_results_target_declared_invariants() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    declared = {
        scenario_id: set(scenario["targets"])
        for scenario_id, scenario in payload["scenarios"].items()
    }

    for result in run_all(sorted(declared)):
        assert set(result.targets) == declared[result.scenario_id]


def test_reordered_events_have_stable_state_hash() -> None:
    first = SCENARIOS["ADV-001"]()
    second = SCENARIOS["ADV-001"]()

    assert first.accepted
    assert first.state_hash == second.state_hash


def test_adversarial_results_emit_required_metrics() -> None:
    required = {
        "determinism_violation",
        "replay_equivalence",
        "divergence_detected",
        "reconciliation_success",
    }

    for result in run_all():
        assert set(result.metrics) == required
        assert all(isinstance(value, bool) for value in result.metrics.values())


def test_concurrent_mutation_conflict_is_deterministic() -> None:
    result = SCENARIOS["ADV-008"]()

    assert result.accepted
    assert not result.metrics["determinism_violation"]
