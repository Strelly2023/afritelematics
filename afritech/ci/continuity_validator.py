from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.simulation.continuity.runner import run_all
from afritech.simulation.continuity.scenarios import SCENARIOS


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "afritech/constitution/CONTINUITY_PROFILE.yaml"
INDEX = ROOT / "afritech/simulation/continuity/index.yaml"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path} must be a mapping")
    return payload


def validate_profile(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "afritech.constitution.continuity_profile.v1":
        fail("continuity profile schema mismatch")

    invariant_class = payload.get("invariant_class")
    if not isinstance(invariant_class, dict):
        fail("continuity profile must define invariant_class")

    if invariant_class.get("id") != "CONTINUITY_INVARIANTS":
        fail("continuity profile must define CONTINUITY_INVARIANTS")

    required_properties = set(invariant_class.get("required_properties", []))
    expected_properties = {
        "identity_continuity",
        "coordination_continuity",
        "economic_participation_continuity",
        "deterministic_recoverability",
    }
    if required_properties != expected_properties:
        fail("continuity invariant required property set mismatch")

    mappings = payload.get("formal_to_operational_mapping")
    if not isinstance(mappings, dict):
        fail("continuity profile must map formal concepts to operational meanings")

    required_mappings = {
        "replay",
        "determinism",
        "witnesses",
        "closed_world",
        "identity_ontology",
        "mutation_governance",
    }
    if set(mappings) != required_mappings:
        fail("continuity profile formal mapping set mismatch")

    disruptions = payload.get("disruption_classes")
    if not isinstance(disruptions, dict) or not disruptions:
        fail("continuity profile must define disruption classes")


def validate_index(
    payload: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[set[str], set[str]]:
    if payload.get("schema") != "afritech.simulation.continuity.index.v1":
        fail("continuity index schema mismatch")

    required_metrics = set(payload.get("metrics", {}).get("required", []))
    expected_metrics = set(profile.get("success_rule", {}).get("valid_if_all", []))
    normalized_expected = {
        "execution_admissible"
        if metric == "execution_remains_admissible"
        else metric
        for metric in expected_metrics
    }

    if required_metrics != normalized_expected:
        fail("continuity index required metrics do not match profile success rule")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        fail("continuity index must define scenarios")

    profile_classes = set(profile.get("disruption_classes", {}))
    indexed_classes = {
        scenario.get("class")
        for scenario in scenarios.values()
        if isinstance(scenario, dict)
    }
    if indexed_classes != profile_classes:
        fail("continuity index disruption classes do not match profile")

    for scenario_id, scenario in scenarios.items():
        if not isinstance(scenario, dict):
            fail(f"{scenario_id} must be a mapping")
        if not scenario.get("targets"):
            fail(f"{scenario_id} must declare target invariants")
        if scenario.get("class") not in profile_classes:
            fail(f"{scenario_id} references unknown disruption class")

    return set(scenarios), required_metrics


def run() -> None:
    profile = load_yaml(PROFILE)
    index = load_yaml(INDEX)

    validate_profile(profile)
    indexed_ids, required_metrics = validate_index(index, profile)

    implemented_ids = set(SCENARIOS)
    missing_implementations = indexed_ids - implemented_ids
    if missing_implementations:
        fail(
            "indexed continuity scenarios missing implementations: "
            f"{sorted(missing_implementations)}"
        )

    orphan_implementations = implemented_ids - indexed_ids
    if orphan_implementations:
        fail(
            "implemented continuity scenarios missing index entries: "
            f"{sorted(orphan_implementations)}"
        )

    results = run_all(sorted(indexed_ids))
    result_ids = {result.scenario_id for result in results}
    if result_ids != indexed_ids:
        fail("continuity execution result set does not match index")

    scenarios = index["scenarios"]
    for result in results:
        declared_targets = set(scenarios[result.scenario_id]["targets"])
        actual_targets = set(result.targets)
        if actual_targets != declared_targets:
            fail(
                f"{result.scenario_id} target mismatch: "
                f"{sorted(actual_targets)} != {sorted(declared_targets)}"
            )

        if set(result.metrics) != required_metrics:
            fail(f"{result.scenario_id} metric set mismatch")

        if not all(isinstance(value, bool) for value in result.metrics.values()):
            fail(f"{result.scenario_id} metrics must be booleans")

        if not all(result.metrics.values()):
            fail(f"{result.scenario_id} did not satisfy all continuity metrics")

        if not result.accepted:
            fail(f"{result.scenario_id} failed: {result.reason}")

        if not result.continuity_hash:
            fail(f"{result.scenario_id} did not emit a continuity hash")

    print("✅ Continuity validation PASSED")
    print(f"✅ Executed disruption scenarios: {len(results)}")
    print(f"✅ Required continuity metrics: {len(required_metrics)}")
    print("✅ Operational survival properties preserve Level 2 guarantees")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Continuity validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
