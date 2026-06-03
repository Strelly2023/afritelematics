"""
afritech.simulation.scale.load_generator

Deterministic event load generator for distributed simulation.

Guarantees:
- Stable event generation across runs
- Controlled routing distribution
- Replay-safe ordering
- Partition-aware workload shaping
"""

from __future__ import annotations

from typing import List, Mapping, Dict, Sequence
from dataclasses import dataclass
import random


# ============================================================
# CONFIG
# ============================================================

@dataclass(frozen=True)
class LoadProfile:
    event_count: int
    routing_space: int  # affects partition distribution
    payload_variation: int  # controls diversity of payload


# ============================================================
# CORE GENERATOR
# ============================================================

def generate_events(
    count: int,
    *,
    routing_space: int = 10,
    payload_variation: int = 5,
) -> List[Mapping[str, object]]:
    """
    Generate deterministic event stream.

    Args:
        count: number of events
        routing_space: how many routing buckets (affects partition spread)
        payload_variation: number of payload patterns

    Returns:
        list of deterministic events
    """

    if count <= 0:
        return []

    events: List[Mapping[str, object]] = []

    for i in range(count):
        events.append(_build_event(i, routing_space, payload_variation))

    return events


# ============================================================
# ADVANCED PROFILES
# ============================================================

def generate_profile(profile: LoadProfile) -> List[Mapping[str, object]]:
    """
    Generate events using a structured profile.
    """
    return generate_events(
        profile.event_count,
        routing_space=profile.routing_space,
        payload_variation=profile.payload_variation,
    )


def generate_partition_skewed_events(
    count: int,
    *,
    hot_partition_bias: int = 3,
) -> List[Mapping[str, object]]:
    """
    Generates skewed load where some partitions receive more traffic.
    Useful for stress testing partition hotspots.
    """

    events: List[Mapping[str, object]] = []

    for i in range(count):
        # skew routing so lower indexes repeat more
        bias_key = i % max(1, (10 // hot_partition_bias))

        routing_key = f"ride.hot.{bias_key:03d}"

        events.append(_build_event_with_key(i, routing_key))

    return events


def generate_burst_events(
    bursts: int,
    burst_size: int,
) -> List[Mapping[str, object]]:
    """
    Generates bursty traffic to simulate sudden load spikes.
    """

    events: List[Mapping[str, object]] = []
    idx = 0

    for b in range(bursts):
        for j in range(burst_size):
            routing_key = f"ride.burst.{b % 10:03d}"
            events.append(_build_event_with_key(idx, routing_key))
            idx += 1

    return events


# ============================================================
# INTERNAL BUILDERS
# ============================================================

def _build_event(
    index: int,
    routing_space: int,
    payload_variation: int,
) -> Dict[str, object]:

    routing_key = f"ride.sim.{index % routing_space:03d}"

    payload_variant = index % payload_variation

    return {
        "event_id": f"event.sim.{index:08d}",
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": _build_payload(index, payload_variant),
    }


def _build_event_with_key(index: int, routing_key: str) -> Dict[str, object]:
    return {
        "event_id": f"event.sim.{index:08d}",
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": _build_payload(index, index % 5),
    }


def _build_payload(index: int, variant: int) -> Dict[str, object]:
    """
    Deterministic payload generator.
    """

    return {
        "rider_id": f"rider.{index:06d}",
        "pickup": _pickup_location(variant),
        "dropoff": _dropoff_location(variant),
        "fare_estimate": _fare_estimate(index, variant),
        "priority": variant % 3,
    }


# ============================================================
# DETERMINISTIC PAYLOAD FEATURES
# ============================================================

def _pickup_location(variant: int) -> str:
    locations = (
        "melbourne.cbd",
        "docklands",
        "southbank",
        "richmond",
        "stkilda",
    )
    return locations[variant % len(locations)]


def _dropoff_location(variant: int) -> str:
    locations = (
        "melbourne.airport",
        "geelong",
        "boxhill",
        "dandenong",
        "sunshine",
    )
    return locations[(variant + 2) % len(locations)]


def _fare_estimate(index: int, variant: int) -> int:
    """
    Fake deterministic pricing.
    """
    base = 20
    return base + ((index + variant) % 15)


# ============================================================
# VALIDATION UTIL
# ============================================================

def validate_determinism(events_a: Sequence[Mapping[str, object]], events_b: Sequence[Mapping[str, object]]) -> bool:
    """
    Ensures two generated event sets are identical.
    """
    return list(events_a) == list(events_b)


class LoadGenerator:
    """Compatibility wrapper for the legacy scale validation surface."""

    def generate(self, count: int, *, seed: int | None = None) -> List[Mapping[str, object]]:
        if seed is None:
            return generate_events(count)

        rng = random.Random(seed)
        events: List[Mapping[str, object]] = []

        for index in range(max(0, count)):
            routing_key = f"ride.sim.{rng.randrange(0, 64):03d}"
            events.append(_build_event_with_key(index, routing_key))

        return events
