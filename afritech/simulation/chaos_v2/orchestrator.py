"""Chaos cycle orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.simulation.chaos_v2.cycle_runner import (
    ChaosCycleResult,
    baseline_hashes,
    run_cycle,
)
from afritech.simulation.chaos_v2.scenario_generator import generate_scenario


@dataclass(frozen=True)
class ChaosRunResult:
    cycle_count: int
    baseline_trace: tuple[Mapping[str, Any], ...]
    baseline_hashes: Mapping[str, str]
    cycles: tuple[ChaosCycleResult, ...]

    @property
    def verified(self) -> bool:
        return len(self.cycles) == self.cycle_count and all(
            cycle.verified for cycle in self.cycles
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "baseline_hashes": dict(self.baseline_hashes),
            "baseline_trace": [_canonicalize(event) for event in self.baseline_trace],
            "cycle_count": self.cycle_count,
            "cycles": [cycle.canonical_dict() for cycle in self.cycles],
            "run_hash": self.run_hash,
            "schema": "afritech.chaos_run_result.v1",
            "verified": self.verified,
        }

    @property
    def run_hash(self) -> str:
        return _canonical_hash(
            {
                "baseline_hashes": dict(self.baseline_hashes),
                "cycle_hashes": [cycle.cycle_hash for cycle in self.cycles],
                "cycle_count": self.cycle_count,
                "verified": self.verified,
            }
        )


def run_chaos_cycles(
    cycle_count: int,
    *,
    base_seed: int = 7303,
) -> ChaosRunResult:
    trace = _baseline_trace()
    hashes = baseline_hashes(trace)
    cycles = tuple(
        run_cycle(
            trace,
            hashes,
            generate_scenario(cycle, base_seed=base_seed, event_count=len(trace)),
        )
        for cycle in range(1, cycle_count + 1)
    )
    return ChaosRunResult(
        baseline_hashes=hashes,
        baseline_trace=trace,
        cycle_count=cycle_count,
        cycles=cycles,
    )


def _baseline_trace() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(6))


def _event(index: int) -> dict[str, Any]:
    identity = "rider.chaos.001" if index < 3 else "driver.chaos.001"
    actions = ("request", "match", "accept", "pickup", "dropoff", "complete")
    return {
        "event_id": f"chaos.event.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": {
            "action": actions[index],
            "ride_id": "ride.chaos.001",
        },
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:00:{index:02d}Z",
    }


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

