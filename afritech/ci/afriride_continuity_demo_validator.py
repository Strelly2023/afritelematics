from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from ecosystems.afriride.continuity.runner import run_all
from ecosystems.afriride.continuity.scenarios import SCENARIOS


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "ecosystems/afriride/continuity/index.yaml"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_index() -> dict[str, Any]:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("AfriRide continuity index must be a mapping")
    return payload


def run() -> None:
    payload = load_index()

    if payload.get("schema") != "ecosystems.afriride.continuity.index.v1":
        fail("AfriRide continuity index schema mismatch")

    positioning = payload.get("positioning")
    if not isinstance(positioning, dict) or not positioning.get("statement"):
        fail("AfriRide continuity index must declare operational positioning")

    forbidden_positioning = positioning.get("forbidden_positioning")
    if not isinstance(forbidden_positioning, list) or not forbidden_positioning:
        fail("AfriRide continuity index must declare forbidden positioning")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        fail("AfriRide continuity index must define scenarios")

    required_metrics = set(payload.get("metrics", {}).get("required", []))
    if not required_metrics:
        fail("AfriRide continuity index must define required metrics")

    indexed_ids = set(scenarios)
    implemented_ids = set(SCENARIOS)
    if indexed_ids != implemented_ids:
        fail(
            "AfriRide continuity scenario index mismatch: "
            f"indexed={sorted(indexed_ids)} implemented={sorted(implemented_ids)}"
        )

    results = run_all(sorted(indexed_ids))
    result_ids = {result.scenario_id for result in results}
    if result_ids != indexed_ids:
        fail("AfriRide continuity result set does not match index")

    for result in results:
        declared_targets = set(scenarios[result.scenario_id]["targets"])
        if set(result.targets) != declared_targets:
            fail(f"{result.scenario_id} target mismatch")

        if set(result.metrics) != required_metrics:
            fail(f"{result.scenario_id} metric set mismatch")

        if not all(isinstance(value, bool) for value in result.metrics.values()):
            fail(f"{result.scenario_id} metrics must be booleans")

        if not all(result.metrics.values()):
            fail(f"{result.scenario_id} did not satisfy all mobility continuity metrics")

        if not result.accepted:
            fail(f"{result.scenario_id} failed: {result.reason}")

        if not result.receipt_hash:
            fail(f"{result.scenario_id} did not emit a receipt hash")

    print("✅ AfriRide continuity demonstration validation PASSED")
    print(f"✅ Operational mobility scenarios: {len(results)}")
    print(f"✅ Required mobility continuity metrics: {len(required_metrics)}")
    print("✅ AfriRide proves continuity behavior without replacing AfriTech doctrine")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ AfriRide continuity demonstration validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
