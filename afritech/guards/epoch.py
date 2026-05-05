from __future__ import annotations

from afritech.state.state import State
from afritech.guards.engine import GuardResult, Guard


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
# Export default epoch guards
# ---------------------------------------------------------------------

EPOCH_GUARDS: tuple[Guard, ...] = (
    require_active_epoch,
    forbid_epoch_mutation,
    forbid_epoch_instance_change,
)