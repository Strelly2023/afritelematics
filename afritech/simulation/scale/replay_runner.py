"""
afritech.simulation.scale.replay_runner

Replay execution to verify deterministic equivalence.

Guarantees:
- execution hash consistency
- order preservation
- full replay determinism
"""

from __future__ import annotations

from typing import List, Dict, Any

from afritech.simulation.scale.run_multi_node import run_simulation


# ============================================================
# CORE REPLAY FUNCTION
# ============================================================

def replay_simulation(
    worker_count: int,
    event_count: int,
    inject_failures: bool = False,
    failure_rate: int = 10,
) -> List[str]:
    """
    Replay uses EXACT same execution pipeline.

    Because the system is deterministic, replay MUST match execution.

    Args:
        worker_count: number of workers
        event_count: number of events
        inject_failures: enable failure injection
        failure_rate: failure frequency

    Returns:
        List of execution hashes
    """

    return run_simulation(
        worker_count=worker_count,
        event_count=event_count,
        inject_failures=inject_failures,
        failure_rate=failure_rate,
    )


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def assert_replay_equivalence(
    execution: List[str],
    replay: List[str],
) -> None:
    """
    Strict equality check between execution and replay.

    Raises AssertionError if mismatch detected.
    """

    assert execution == replay, (
        "Replay mismatch detected.\n"
        f"Execution length: {len(execution)}\n"
        f"Replay length: {len(replay)}"
    )


def compare_runs(
    *,
    worker_count: int,
    event_count: int,
    inject_failures: bool = False,
    failure_rate: int = 10,
) -> Dict[str, Any]:
    """
    Runs execution + replay and returns structured comparison.

    Useful for diagnostics or reporting.
    """

    execution = run_simulation(
        worker_count=worker_count,
        event_count=event_count,
        inject_failures=inject_failures,
        failure_rate=failure_rate,
    )

    replay = replay_simulation(
        worker_count=worker_count,
        event_count=event_count,
        inject_failures=inject_failures,
        failure_rate=failure_rate,
    )

    return {
        "match": execution == replay,
        "execution_length": len(execution),
        "replay_length": len(replay),
        "worker_count": worker_count,
        "event_count": event_count,
        "inject_failures": inject_failures,
        "failure_rate": failure_rate,
    }


# ============================================================
# SELF-TESTS (PYTEST COMPATIBLE)
# ============================================================

def test_replay_equivalence_basic():
    execution = run_simulation(worker_count=5, event_count=100)
    replay = replay_simulation(worker_count=5, event_count=100)

    assert_replay_equivalence(execution, replay)


def test_replay_equivalence_with_failures():
    execution = run_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
        failure_rate=5,
    )

    replay = replay_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
        failure_rate=5,
    )

    assert_replay_equivalence(execution, replay)


def test_replay_scaling_invariance():
    execution = run_simulation(worker_count=4, event_count=120)
    replay = replay_simulation(worker_count=10, event_count=120)

    assert execution == replay


def test_replay_extreme_failure():
    execution = run_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
        failure_rate=2,
    )

    replay = replay_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
        failure_rate=2,
    )

    assert execution == replay