from __future__ import annotations

from pathlib import Path

import yaml

from ecosystems.afriride.continuity.runner import run_all
from ecosystems.afriride.continuity.scenarios import REQUIRED_METRICS, SCENARIOS


INDEX = Path("ecosystems/afriride/continuity/index.yaml")


def test_all_indexed_afriride_continuity_scenarios_execute() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    indexed = set(payload["scenarios"])

    assert indexed == set(SCENARIOS)

    results = run_all(sorted(indexed))

    assert len(results) == len(indexed)
    assert all(result.accepted for result in results)


def test_afriride_continuity_metrics_are_complete() -> None:
    required = set(REQUIRED_METRICS)

    for result in run_all():
        assert set(result.metrics) == required
        assert all(result.metrics.values())
        assert result.receipt_hash


def test_afriride_continuity_targets_match_index() -> None:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    declared = {
        scenario_id: set(scenario["targets"])
        for scenario_id, scenario in payload["scenarios"].items()
    }

    for result in run_all(sorted(declared)):
        assert set(result.targets) == declared[result.scenario_id]


def test_adversarial_coordination_rejects_duplicate_authority() -> None:
    result = SCENARIOS["AFRIRIDE-CONT-003"]()

    assert result.accepted
    assert result.metrics["authority_conflict_prevented"]
