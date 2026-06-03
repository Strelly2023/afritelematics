"""
afritech.simulation.scale.partition_drift_probe

Checks whether partition assignment is stable across runs.

Guarantees:
- no partition drift
- routing determinism
- replay-safe partitioning
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from afritech.distributed.api.partition import (
    default_partition_registry,
    assign_partition,
)

from afritech.simulation.scale.load_generator import generate_events


# ============================================================
# CORE CAPTURE
# ============================================================

def capture_partition_mapping(event_count: int) -> Dict[str, str]:
    """
    Returns mapping:
        event_id -> partition_id
    """

    registry = default_partition_registry()
    events = generate_events(event_count)

    mapping: Dict[str, str] = {}

    for e in events:
        assignment = assign_partition(
            routing_key=e["routing_key"],
            routing_scope=e["routing_scope"],
            registry=registry,
        )
        mapping[e["event_id"]] = assignment.partition_id

    return mapping


# ============================================================
# DISTRIBUTION ANALYSIS
# ============================================================

def compute_partition_distribution(
    mapping: Dict[str, str]
) -> Dict[str, int]:
    """
    Compute number of events per partition.
    """

    counts: Dict[str, int] = {}

    for partition_id in mapping.values():
        counts[partition_id] = counts.get(partition_id, 0) + 1

    return counts


# ============================================================
# DRIFT DETECTION
# ============================================================

def detect_partition_drift(
    mapping_a: Dict[str, str],
    mapping_b: Dict[str, str],
) -> List[Tuple[str, str, str]]:
    """
    Detects partition drift between two mappings.

    Returns:
        List of (event_id, partition_a, partition_b)
    """

    drift: List[Tuple[str, str, str]] = []

    for event_id in mapping_a:

        p1 = mapping_a[event_id]
        p2 = mapping_b.get(event_id)

        if p2 is None:
            drift.append((event_id, p1, "MISSING"))
        elif p1 != p2:
            drift.append((event_id, p1, p2))

    return drift


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def assert_no_partition_drift(
    mapping_a: Dict[str, str],
    mapping_b: Dict[str, str],
) -> None:
    """
    Raises AssertionError if drift detected.
    """

    drift = detect_partition_drift(mapping_a, mapping_b)

    assert not drift, (
        f"Partition drift detected: {len(drift)} events differ\n"
        f"Sample: {drift[:5]}"
    )


def assert_partition_distribution_equal(
    mapping_a: Dict[str, str],
    mapping_b: Dict[str, str],
) -> None:
    """
    Ensures partition load distribution is identical.
    """

    dist_a = compute_partition_distribution(mapping_a)
    dist_b = compute_partition_distribution(mapping_b)

    assert dist_a == dist_b, (
        "Partition distribution mismatch\n"
        f"A: {dist_a}\n"
        f"B: {dist_b}"
    )


# ============================================================
# SELF-TESTS (PYTEST COMPATIBLE)
# ============================================================

def test_capture_consistency():
    m1 = capture_partition_mapping(100)
    m2 = capture_partition_mapping(100)

    assert_no_partition_drift(m1, m2)


def test_large_scale_partition_stability():
    m1 = capture_partition_mapping(500)
    m2 = capture_partition_mapping(500)

    assert_no_partition_drift(m1, m2)


def test_distribution_consistency():
    m1 = capture_partition_mapping(300)
    m2 = capture_partition_mapping(300)

    assert_partition_distribution_equal(m1, m2)


def test_multiple_runs_consistency():
    runs = [
        capture_partition_mapping(200)
        for _ in range(3)
    ]

    assert runs[0] == runs[1] == runs[2]
