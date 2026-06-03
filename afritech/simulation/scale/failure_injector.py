"""
afritech.simulation.scale.failure_injector

Deterministic failure injection for distributed simulation.

Guarantees:
- Failure behavior is deterministic
- Does not introduce nondeterminism
- Failures are replay-safe
- No corruption of execution correctness
"""

from __future__ import annotations

from typing import Optional, Sequence


# ============================================================
# EXCEPTION
# ============================================================

class SimulatedWorkerFailure(Exception):
    """
    Controlled failure used only during simulation.
    """
    pass


# ============================================================
# CONFIG
# ============================================================

class FailurePolicy:
    """
    Deterministic failure policy.
    """

    def __init__(
        self,
        *,
        fail_every_n: int = 10,
        enabled: bool = True,
    ):
        if fail_every_n <= 0:
            raise ValueError("fail_every_n must be > 0")

        self.fail_every_n = fail_every_n
        self.enabled = enabled


# ============================================================
# CORE INJECTOR
# ============================================================

def maybe_inject_worker_failure(
    worker,
    index: int,
    *,
    policy: Optional[FailurePolicy] = None,
):
    """
    Deterministically inject a failure into a worker execution.
    """

    if policy is None:
        policy = FailurePolicy()

    if not policy.enabled:
        return

    if index % policy.fail_every_n == 0:
        raise SimulatedWorkerFailure(
            f"Injected failure at index={index} for worker={_safe_worker_id(worker)}"
        )


# ============================================================
# SAFE WRAPPER EXECUTION
# ============================================================

def safe_execute_with_injection(
    worker,
    record,
    index: int,
    *,
    policy: Optional[FailurePolicy] = None,
):
    """
    Executes worker with failure injection but ensures safe fallback.

    Guarantees:
    - fail-closed behavior
    - no invalid output
    """

    try:
        maybe_inject_worker_failure(worker, index, policy=policy)
        return worker.execute(record)

    except SimulatedWorkerFailure:
        return None  # ✅ fail-closed


# ============================================================
# ADVANCED FAILURE MODES
# ============================================================

def maybe_delay_execution(
    index: int,
    *,
    delay_factor: int = 5,
) -> None:
    """
    Simulates logical delay (no real time.sleep to preserve determinism).
    """

    if delay_factor > 0 and index % delay_factor == 0:
        pass  # flag only


def maybe_skip_execution(
    index: int,
    *,
    skip_every_n: int = 15,
) -> bool:
    """
    Simulates dropped messages.
    """
    if skip_every_n <= 0:
        return False

    return index % skip_every_n == 0


def maybe_duplicate_execution(
    index: int,
    *,
    duplicate_every_n: int = 20,
) -> bool:
    """
    Simulates duplicate delivery.
    """
    if duplicate_every_n <= 0:
        return False

    return index % duplicate_every_n == 0


# ============================================================
# COMBINED FAILURE STRATEGY
# ============================================================

def apply_failure_strategy(
    worker,
    record,
    index: int,
    policy: Optional[FailurePolicy] = None,
):
    """
    Combined deterministic failure strategy.

    Applies:
    - skip
    - crash
    - duplicate

    Always deterministic for same index + policy.
    """

    if policy is None:
        policy = FailurePolicy()

    # ---------------------------------------------------------
    # Skip (drop task)
    # ---------------------------------------------------------
    if maybe_skip_execution(index):
        return []

    outputs = []

    # ---------------------------------------------------------
    # Primary execution
    # ---------------------------------------------------------
    result = safe_execute_with_injection(
        worker,
        record,
        index,
        policy=policy,  # ✅ propagate policy
    )

    if result is not None:
        outputs.append(result)

    # ---------------------------------------------------------
    # Duplicate execution
    # ---------------------------------------------------------
    if maybe_duplicate_execution(index):

        # NOTE: shift index to avoid identical collision
        duplicate_index = index + policy.fail_every_n

        duplicate_result = safe_execute_with_injection(
            worker,
            record,
            duplicate_index,
            policy=policy,  # ✅ propagate policy
        )

        if duplicate_result is not None:
            outputs.append(duplicate_result)

    return outputs


# ============================================================
# INTERNAL
# ============================================================

def _safe_worker_id(worker) -> str:
    if worker is None:
        return "unknown"

    return getattr(worker, "worker_id", "unknown")


class FailureInjector:
    """Compatibility wrapper for legacy deterministic worker survival tests."""

    def kill_workers(
        self,
        workers: Sequence[str],
        *,
        percentage: float,
    ) -> tuple[str, ...]:
        if percentage <= 0:
            return tuple(workers)

        if percentage >= 1:
            return ()

        kill_count = int(len(workers) * percentage)
        survivors = tuple(workers[kill_count:])

        return survivors or tuple(workers[-1:])
