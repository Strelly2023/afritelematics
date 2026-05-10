# afritech/internal/state_mutation/apply_state_transition.py

"""
AfriTech Internal State Mutation
================================

This module contains mutation-capable state transition logic.

CRITICAL CONSTITUTIONAL RULES:
- This module MUST NOT be imported outside the constitutional gateway
- This module MUST enforce runtime admissibility
- This module MUST NOT perform constitutional validation
- This module MUST NOT infer authority or epoch
- This module MUST be pure in effect: input state → output state

Any violation of these rules is a constitutional failure.
"""

from __future__ import annotations

from afritech.internal.admissibility import assert_caller_is_constitutional_gateway
from afritech.state.state import State


# ---------------------------------------------------------------------
# STATE TRANSITION (MUTATION-CAPABLE)
# ---------------------------------------------------------------------

def apply_state_transition(
    parent_state: State,
    *,
    mutation_payload: dict,
) -> State:
    """
    Apply a state transition to produce a new state.

    This function:
    - performs NO constitutional checks
    - performs NO authority checks
    - performs NO epoch checks
    - performs NO replay checks

    All such checks MUST be performed by the constitutional gateway
    before this function is called.

    Runtime admissibility is enforced here.
    """

    # 🔒 RUNTIME TOPOLOGY ENFORCEMENT
    assert_caller_is_constitutional_gateway()

    # Defensive copy — mutation must not alter parent state in place
    child_state = parent_state.clone()

    # Apply mutation payload
    # NOTE: the semantics of apply() belong to the State model
    child_state.apply(mutation_payload)

    return child_state