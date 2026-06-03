"""
afritech.simulation.scale.recovery_storm

Simulates repeated failure + recovery cycles.

Guarantees:
- deterministic recovery
- replay-safe convergence
- stable outputs across repeated storms
"""

from __future__ import annotations

from typing import List

from afritech.simulation.scale.run_multi_node import run_simulation


# ============================================================
# CORE STORM RUNNER
# ============================================================

def run_recovery_storm(
    cycles: int,
    *,
    worker_count: int,
    event_count: int,
    failure_rate: int,
) -> List[List[str]]:
    """
    Runs multiple recovery cycles.

    Each cycle simulates:
    - execution
    - failures
    - implicit replay-based recovery

    Args:
        cycles: number of recovery cycles
        worker_count: number of workers
        event_count: number of events
        failure_rate: failure injection frequency

    Returns:
        List of execution result lists (one per cycle)
    """

    if cycles <= 0:
        raise ValueError("cycles must be > 0")

    results: List[List[str]] = []

    for _ in range(cycles):
        run = run_simulation(
            worker_count=worker_count,
            event_count=event_count,
            inject_failures=True,
            failure_rate=failure_rate,
        )
        results.append(run)

    return results


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def assert_recovery_convergence(
    runs: List[List[str]]
) -> None:
    """
    Ensures all recovery cycles produce identical results.
    """

    if not runs:
        raise AssertionError("No runs provided")

    first = runs[0]

    for i, r in enumerate(runs[1:], start=1):
        assert r == first, (
            f"Recovery divergence detected at cycle {i}\n"
            f"Expected length: {len(first)}\n"
            f"Actual length: {len(r)}"
        )


def is_recovery_stable(runs: List[List[str]]) -> bool:
    """
    Returns True if all runs are identical.
    """
    if not runs:
        return True

    first = runs[0]
    return all(r == first for r in runs)


# ============================================================
# DIAGNOSTIC UTILITIES
# ============================================================

def summarize_storm(
    runs: List[List[str]]
) -> dict:
    """
    Returns structured summary for debugging or reporting.
    """

    if not runs:
        return {
            "cycles": 0,
            "stable": True,
            "lengths": [],
        }

    lengths = [len(r) for r in runs]

    return {
        "cycles": len(runs),
        "stable": is_recovery_stable(runs),
        "lengths": lengths,
        "min_length": min(lengths),
        "max_length": max(lengths),
    }


# ============================================================
# SELF TESTS (PYTEST COMPATIBLE)
# ============================================================

def test_recovery_basic():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=5,
        event_count=100,
        failure_rate=5,
    )

    assert_recovery_convergence(runs)


def test_recovery_extreme_failure():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=8,
        event_count=200,
        failure_rate=2,
    )

    assert_recovery_convergence(runs)


def test_recovery_scaling_consistency():
    small = run_recovery_storm(
        cycles=2,
        worker_count=3,
        event_count=150,
        failure_rate=4,
    )

    large = run_recovery_storm(
        cycles=2,
        worker_count=12,
        event_count=150,
        failure_rate=4,
    )

    assert small[0] == large[0]


def test_recovery_output_valid():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=5,
        event_count=120,
        failure_rate=4,
    )

    for run in runs:
        assert isinstance(run, list)
        assert all(isinstance(x, str) for x in run)
        assert all(len(x) > 0 for x in run)