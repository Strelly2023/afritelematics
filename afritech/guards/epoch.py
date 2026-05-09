# afritech/guards/epoch.py

from __future__ import annotations

from typing import Callable

from afritech.state.state import State
from afritech.guards.guard_core import GuardResult
from afritech.guards.engine import fail, ViolationClass


# ---------------------------------------------------------------------
# INTERNAL HELPER (same pattern as authority.py)
# ---------------------------------------------------------------------

def enforce_guard_result(result: GuardResult):
    """
    Convert GuardResult into constitutional enforcement.
    """

    if not result.ok:
        fail(
            result.reason or "epoch_violation",
            ViolationClass.A_FATAL,
        )


# ---------------------------------------------------------------------
# ADAPTER: functional guard → enforcing guard
# ---------------------------------------------------------------------

def with_epoch_guard(guard_fn: Callable):
    """
    Wrap a functional epoch guard into an enforcing guard.
    """

    def guard(state: State, transition):

        result = guard_fn(state, transition)

        if not isinstance(result, GuardResult):
            fail(
                "invalid_guard_result_type",
                ViolationClass.B_STRUCTURAL,
            )

        enforce_guard_result(result)

        return True

    return guard


# ---------------------------------------------------------------------
# Guard: Active epoch required
# ---------------------------------------------------------------------

def require_active_epoch(state: State, transition) -> GuardResult:

    if not state.epoch.active:
        return GuardResult(False, "NO_ACTIVE_EPOCH")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Guard: Epoch cannot change implicitly
# ---------------------------------------------------------------------

def forbid_epoch_mutation(state: State, transition) -> GuardResult:

    candidate = transition(state)

    if candidate.epoch != state.epoch:
        return GuardResult(False, "EPOCH_MUTATION_FORBIDDEN")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Guard: Epoch instance must be stable
# ---------------------------------------------------------------------

def forbid_epoch_instance_change(state: State, transition) -> GuardResult:

    candidate = transition(state)

    if candidate.epoch.instance_id != state.epoch.instance_id:
        return GuardResult(False, "EPOCH_INSTANCE_CHANGE_FORBIDDEN")

    return GuardResult(True)


# ---------------------------------------------------------------------
# Export enforcing guards (IMPORTANT)
# ---------------------------------------------------------------------

EPOCH_GUARDS = (
    with_epoch_guard(require_active_epoch),
    with_epoch_guard(forbid_epoch_mutation),
    with_epoch_guard(forbid_epoch_instance_change),
)