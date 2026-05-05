from __future__ import annotations

from typing import Callable

from afritech.state.state import State
from afritech.state.snapshot import freeze_state
from afritech.state.equality import compute_state_hash
from afritech.state.types import TransitionId


# A transition is a pure function from State → State
Transition = Callable[[State], State]

def apply_transition(
    state: State,
    transition: Transition,
    transition_id: TransitionId,
) -> State:
    """
    Apply a transition in a fully controlled, deterministic way.

    Guarantees:
    - input state is frozen
    - output state is frozen
    - provenance is correctly linked
    - state hash is recomputed
    """

    # -----------------------------------------------------------------
    # 1. Freeze input (enforce immutability boundary)
    # -----------------------------------------------------------------
    state = freeze_state(state)

    # -----------------------------------------------------------------
    # 2. Apply transition (pure function)
    # -----------------------------------------------------------------
    new_state = transition(state)

    # -----------------------------------------------------------------
    # 3. Freeze output
    # -----------------------------------------------------------------
    new_state = freeze_state(new_state)

    # -----------------------------------------------------------------
    # 4. Compute new state hash
    # -----------------------------------------------------------------
    new_hash = compute_state_hash(new_state)

    # -----------------------------------------------------------------
    # 5. Attach provenance + attestation
    # -----------------------------------------------------------------
    return State(
        kernel_hash=new_state.kernel_hash,
        epoch=new_state.epoch,

        registry=new_state.registry,
        vm=new_state.vm,
        governance=new_state.governance,

        provenance=type(new_state.provenance)(
            parent_hash=compute_state_hash(state),
            transition_id=transition_id,
        ),

        attestation=type(new_state.attestation)(
            state_hash=new_hash,
            verified=False,  # verification happens later
        ),
    )