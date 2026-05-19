from __future__ import annotations

from pathlib import Path

import yaml

from afritech.simulation.continuity.runner import run_all
from afritech.simulation.continuity.scenarios import REQUIRED_METRICS, SCENARIOS


INDEX = Path("afritech/simulation/continuity/index.yaml")


def test_all_indexed_continuity_scenarios_execute() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    indexed = set(payload["scenarios"])

    assert indexed == set(SCENARIOS)

    results = run_all(sorted(indexed))

    assert len(results) == len(indexed)
    assert all(result.accepted for result in results)


def test_continuity_results_target_declared_invariants() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    declared = {
        scenario_id: set(scenario["targets"])
        for scenario_id, scenario in payload["scenarios"].items()
    }

    for result in run_all(sorted(declared)):
        assert set(result.targets) == declared[result.scenario_id]


def test_continuity_results_emit_required_metrics() -> None:
    required = set(REQUIRED_METRICS)

    for result in run_all():
        assert set(result.metrics) == required
        assert all(isinstance(value, bool) for value in result.metrics.values())
        assert all(result.metrics.values())


def test_partition_survival_has_stable_continuity_hash() -> None:
    first = SCENARIOS["CONT-001"]()
    second = SCENARIOS["CONT-001"]()

    assert first.accepted
    assert first.continuity_hash == second.continuity_hash
