from __future__ import annotations

import json
import sys
from typing import Iterable

from ecosystems.afriride.continuity.models import AfriRideContinuityResult
from ecosystems.afriride.continuity.scenarios import SCENARIOS


def run_all(
    selected: Iterable[str] | None = None,
) -> tuple[AfriRideContinuityResult, ...]:
    scenario_ids = tuple(selected) if selected is not None else tuple(sorted(SCENARIOS))
    results = []

    for scenario_id in scenario_ids:
        if scenario_id not in SCENARIOS:
            raise KeyError(f"unknown AfriRide continuity scenario: {scenario_id}")
        results.append(SCENARIOS[scenario_id]())

    return tuple(results)


def main() -> int:
    results = run_all()
    payload = [result.to_dict() for result in results]
    print(json.dumps(payload, sort_keys=True, indent=2))

    if not all(result.accepted for result in results):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
