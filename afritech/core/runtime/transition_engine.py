# afritech/runtime/transition_engine.py

from __future__ import annotations

"""
AfriTech Runtime Transition Engine
=================================

Authoritative state transition applicator.

Responsibilities:
- apply pure State → State transitions
- enforce immutability boundaries
- bind provenance deterministically
- recompute state hashes
- emit TRACE for causal state evolution

IMPORTANT:
- This module performs NO guard evaluation
- This module performs NO admission checks
- This module assumes guards already passed
"""

from typing import Callable, Optional

from afritech.state.state import State
from afritech.state.snapshot import freeze_state
from afritech.state.equality import compute_state_hash
from afritech.state.types import TransitionId

from afritech.trace.trace_engine import TraceEngine


# ---------------------------------------------------------------------
# Transition type
# ---------------------------------------------------------------------

# A transition is a pure function from State → State
Transition = Callable[[State], State]


# ---------------------------------------------------------------------
# Transition application
# ---------------------------------------------------------------------

def apply_transition(
    state: State,
    transition: Transition,
    transition_id: TransitionId,
    *,
    trace: Optional[TraceEngine] = None,
) -> State:
    """
    Apply a transition in a fully controlled, deterministic way.

    Guarantees:
    - input state is frozen (immutability boundary)
    - output state is frozen
    - provenance is correctly linked
    - state hash is recomputed deterministically
    - TRACE binds causal state evolution
    """

    # -------------------------------------------------------------
    # TRACE: start state transition
    # -------------------------------------------------------------

    if trace:
        trace.record(
            "state_transition_start",
            {
                "state_hash": compute_state_hash(state),
                "transition_id": str(transition_id),
            },
        )

    # -------------------------------------------------------------
    # 1. Freeze input (immutability boundary)
    # -------------------------------------------------------------

    frozen_state = freeze_state(state)

    # -------------------------------------------------------------
    # 2. Apply transition (pure function)
    # -------------------------------------------------------------

    new_state = transition(frozen_state)

    # -------------------------------------------------------------
    # 3. Freeze output
    # -------------------------------------------------------------

    frozen_new_state = freeze_state(new_state)

    # -------------------------------------------------------------
    # 4. Compute new state hash
    # -------------------------------------------------------------

    new_state_hash = compute_state_hash(frozen_new_state)
    parent_state_hash = compute_state_hash(frozen_state)

    # -------------------------------------------------------------
    # 5. Attach provenance + attestation
    # -------------------------------------------------------------

    result_state = State(
        kernel_hash=frozen_new_state.kernel_hash,
        epoch=frozen_new_state.epoch,

        registry=frozen_new_state.registry,
        vm=frozen_new_state.vm,
        governance=frozen_new_state.governance,

        provenance=type(frozen_new_state.provenance)(
            parent_hash=parent_state_hash,
            transition_id=transition_id,
        ),

        attestation=type(frozen_new_state.attestation)(
            state_hash=new_state_hash,
            verified=False,  # verification occurs later
        ),
    )

    # -------------------------------------------------------------
    # TRACE: complete state transition
    # -------------------------------------------------------------

    if trace:
        trace.complete(
            "state_transition_start",
            {
                "parent_state_hash": parent_state_hash,
                "new_state_hash": new_state_hash,
            },
        )

    return result_state