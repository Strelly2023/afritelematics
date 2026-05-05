from __future__ import annotations

from typing import Callable

from afritech.state.state import State
from afritech.state.snapshot import freeze_state
from afritech.state.equality import compute_state_hash
from afritech.state.types import TransitionId


# ---------------------------------------------------------------------
# Transition type
# ---------------------------------------------------------------------

# A Transition is a pure function from State → State
Transition = Callable[[State], State]


# ---------------------------------------------------------------------
# Core transition engine (唯一合法状态生产器)
# ---------------------------------------------------------------------

def apply_transition(
    state: State,
    transition: Transition,
    transition_id: TransitionId,
) -> State:
    """
    Apply a transition in a fully controlled, deterministic way.

    Guarantees:
    - input state is frozen
    - transition is pure
    - output state is frozen
    - provenance is enforced
    - state hash is recomputed
    """

    # -----------------------------------------------------------------
    # 1. Freeze input (immutability boundary)
    # -----------------------------------------------------------------
    frozen_state = freeze_state(state)

    # -----------------------------------------------------------------
    # 2. Apply transition (pure function)
    # -----------------------------------------------------------------
    candidate_state = transition(frozen_state)

    # -----------------------------------------------------------------
    # 3. Freeze output
    # -----------------------------------------------------------------
    frozen_candidate = freeze_state(candidate_state)

    # -----------------------------------------------------------------
    # 4. Compute hashes
    # -----------------------------------------------------------------
    parent_hash = compute_state_hash(frozen_state)
    new_hash = compute_state_hash(frozen_candidate)

    # -----------------------------------------------------------------
    # 5. Reconstruct State with enforced provenance + attestation
    # -----------------------------------------------------------------
    return State(
        kernel_hash=frozen_candidate.kernel_hash,
        epoch=frozen_candidate.epoch,

        registry=frozen_candidate.registry,
        vm=frozen_candidate.vm,
        governance=frozen_candidate.governance,

        provenance=type(frozen_candidate.provenance)(
            parent_hash=parent_hash,
            transition_id=transition_id,
        ),

        attestation=type(frozen_candidate.attestation)(
            state_hash=new_hash,
            verified=False,
        ),
    )