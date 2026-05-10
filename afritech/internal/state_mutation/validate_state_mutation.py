# afritech/internal/state_mutation/validate_state_mutation.py

"""
AfriTech Internal State Mutation Validation
==========================================

This module performs PRE-MUTATION validation for state changes.

CRITICAL CONSTITUTIONAL POSITIONING:
- This module MAY inspect mutation intent
- This module MUST NOT mutate state
- This module MUST NOT enforce constitutional law
- This module MUST enforce runtime admissibility
- This module MUST NOT infer authority, epoch, or registry state

Its sole purpose is to prevent malformed or structurally invalid
mutations from reaching the mutation layer.

Constitutional legality is enforced elsewhere.
"""

from __future__ import annotations

from typing import Mapping, Any

from afritech.internal.admissibility import assert_caller_is_constitutional_gateway
from afritech.state.state import State


# ---------------------------------------------------------------------
# STATE MUTATION VALIDATION (NON-MUTATING)
# ---------------------------------------------------------------------

def validate_state_mutation(
    *,
    parent_state: State,
    mutation_payload: Mapping[str, Any],
) -> None:
    """
    Validate that a proposed mutation payload is structurally
    compatible with the parent state.

    This function:
    - performs NO state mutation
    - performs NO constitutional checks
    - performs NO authority checks
    - performs NO epoch checks
    - raises immediately on invalid structure

    It returns NOTHING.
    Any failure MUST raise an exception.

    Runtime admissibility is enforced here.
    """

    # 🔒 RUNTIME TOPOLOGY ENFORCEMENT
    assert_caller_is_constitutional_gateway()

    # -----------------------------------------------------------------
    # BASIC STRUCTURAL VALIDATION
    # -----------------------------------------------------------------

    if not isinstance(parent_state, State):
        raise TypeError(
            "parent_state must be an instance of State"
        )

    if not isinstance(mutation_payload, Mapping):
        raise TypeError(
            "mutation_payload must be a mapping (dict-like)"
        )

    if not mutation_payload:
        raise ValueError(
            "mutation_payload must not be empty"
        )

    # -----------------------------------------------------------------
    # PAYLOAD COMPATIBILITY CHECKS
    # -----------------------------------------------------------------

    # The exact semantics depend on your State model.
    # This assumes State exposes a schema or validation hook.
    # If not present, this function should be extended,
    # NOT bypassed.

    if hasattr(parent_state, "validate_mutation"):
        parent_state.validate_mutation(mutation_payload)
    elif hasattr(parent_state, "schema"):
        for key in mutation_payload.keys():
            if key not in parent_state.schema:
                raise ValueError(
                    f"Mutation key '{key}' not permitted by state schema"
                )
    else:
        # Minimal fallback: ensure keys are strings
        for key in mutation_payload.keys():
            if not isinstance(key, str):
                raise ValueError(
                    "All mutation_payload keys must be strings"
                )