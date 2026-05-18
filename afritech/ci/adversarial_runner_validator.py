from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.simulation.adversarial.runner import run_all
from afritech.simulation.adversarial.scenarios import SCENARIOS


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "afritech/simulation/adversarial/index.yaml"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_index() -> dict[str, Any]:
    payload = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("adversarial index must be a mapping")
    return payload


def run() -> None:
    payload = load_index()
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        fail("adversarial index must define scenarios")

    required_metrics = set(
        payload.get("metrics", {}).get("required", [])
    )
    if not required_metrics:
        fail("adversarial index must define required metrics")

    indexed_ids = set(scenarios)
    implemented_ids = set(SCENARIOS)

    missing_implementations = indexed_ids - implemented_ids
    if missing_implementations:
        fail(
            "indexed adversarial scenarios missing implementations: "
            f"{sorted(missing_implementations)}"
        )

    orphan_implementations = implemented_ids - indexed_ids
    if orphan_implementations:
        fail(
            "implemented adversarial scenarios missing index entries: "
            f"{sorted(orphan_implementations)}"
        )

    results = run_all(sorted(indexed_ids))
    result_ids = {result.scenario_id for result in results}
    if result_ids != indexed_ids:
        fail("adversarial execution result set does not match index")

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

        if not result.accepted:
            fail(f"{result.scenario_id} failed: {result.reason}")

    print("✅ Adversarial runner validation PASSED")
    print(f"✅ Executed scenarios: {len(results)}")
    print(f"✅ Required metrics: {len(required_metrics)}")
    print("✅ Scenario targets and metrics match index")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Adversarial runner validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
