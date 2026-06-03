"""Deterministic randomized chaos scenario generation."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Mapping


DISTURBANCE_TYPES = (
    "partition",
    "delay",
    "duplicate",
    "corruption",
)

INCOMPLETENESS_TYPES = (
    "remove_early",
    "remove_mid",
    "remove_tail",
)

RECOVERY_VARIANTS = (
    "immediate",
    "delayed",
    "partial",
    "multi_source_merge",
)


@dataclass(frozen=True)
class ChaosScenario:
    cycle: int
    seed: int
    disturbance_type: str
    incompleteness_type: str
    recovery_variant: str
    delay_magnitude: int
    corruption_sequence: int
    partition_topology: str
    removed_sequences: tuple[int, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "corruption_sequence": self.corruption_sequence,
            "cycle": self.cycle,
            "delay_magnitude": self.delay_magnitude,
            "disturbance_type": self.disturbance_type,
            "incompleteness_type": self.incompleteness_type,
            "partition_topology": self.partition_topology,
            "recovery_variant": self.recovery_variant,
            "removed_sequences": list(self.removed_sequences),
            "seed": self.seed,
        }


def generate_scenario(
    cycle: int,
    *,
    base_seed: int = 7303,
    event_count: int = 6,
) -> ChaosScenario:
    rng = random.Random(base_seed + cycle)
    incompleteness_type = rng.choice(INCOMPLETENESS_TYPES)
    return ChaosScenario(
        corruption_sequence=rng.randrange(event_count),
        cycle=cycle,
        delay_magnitude=rng.randint(1, 25),
        disturbance_type=rng.choice(DISTURBANCE_TYPES),
        incompleteness_type=incompleteness_type,
        partition_topology=f"partition.split.{rng.randint(1, 4)}",
        recovery_variant=rng.choice(RECOVERY_VARIANTS),
        removed_sequences=_removed_sequences(rng, incompleteness_type, event_count),
        seed=base_seed + cycle,
    )


def apply_disturbance(
    trace: tuple[Mapping[str, Any], ...],
    scenario: ChaosScenario,
) -> tuple[Mapping[str, Any], ...]:
    events = [dict(event) for event in trace]
    if scenario.disturbance_type == "partition":
        index = scenario.corruption_sequence
        events[index] = {
            **events[index],
            "partition_id": scenario.partition_topology,
            "received_order": int(events[index]["sequence"]) + scenario.delay_magnitude,
        }
    elif scenario.disturbance_type == "delay":
        index = scenario.corruption_sequence
        events[index] = {
            **events[index],
            "received_order": int(events[index]["sequence"]) + scenario.delay_magnitude,
        }
    elif scenario.disturbance_type == "duplicate":
        index = scenario.corruption_sequence
        events.insert(index, dict(events[index]))
    elif scenario.disturbance_type == "corruption":
        index = scenario.corruption_sequence
        events.insert(
            index,
            {
                **events[index],
                "corrupted": True,
                "payload": {
                    "canonical_replay_hash": "forged",
                    "ride_id": "ride.chaos.001",
                },
            },
        )
    return tuple(events)


def apply_incompleteness(
    trace: tuple[Mapping[str, Any], ...],
    scenario: ChaosScenario,
) -> tuple[Mapping[str, Any], ...]:
    removed = set(scenario.removed_sequences)
    return tuple(event for event in trace if int(event["sequence"]) not in removed)


def recovery_trace(
    full_trace: tuple[Mapping[str, Any], ...],
    scenario: ChaosScenario,
) -> tuple[Mapping[str, Any], ...]:
    removed = tuple(
        event for event in full_trace if int(event["sequence"]) in scenario.removed_sequences
    )
    if scenario.recovery_variant == "partial":
        return removed[:1]
    if scenario.recovery_variant == "multi_source_merge":
        return (*removed[:1], *full_trace, *removed[1:])
    return removed


def _removed_sequences(
    rng: random.Random,
    incompleteness_type: str,
    event_count: int,
) -> tuple[int, ...]:
    if incompleteness_type == "remove_early":
        return (rng.randrange(0, max(1, event_count // 3)),)
    if incompleteness_type == "remove_tail":
        return (rng.randrange(max(1, event_count - 2), event_count),)
    start = rng.randrange(1, max(2, event_count - 2))
    return tuple(range(start, min(event_count, start + rng.randint(1, 2))))

