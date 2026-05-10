# afritech/internal/epoch_mutation/advance_epoch.py

"""
AfriTech Internal Epoch Mutation
================================

This module contains mutation-capable epoch advancement logic.

CRITICAL CONSTITUTIONAL RULES:
- This module MUST NOT be imported outside the constitutional gateway
- This module MUST enforce runtime admissibility
- This module MUST NOT enforce constitutional law
- This module MUST NOT infer authority, registry, or policy
- This module MUST perform only epoch mutation mechanics

Epoch legality (ADR presence, monotonicity, reseal rules, etc.)
is enforced exclusively by constitutional profiles and the gateway.
"""

from __future__ import annotations

from afritech.internal.admissibility import assert_caller_is_constitutional_gateway


# ---------------------------------------------------------------------
# EPOCH ADVANCEMENT (MUTATION-CAPABLE)
# ---------------------------------------------------------------------

def advance_epoch(
    current_epoch,
    *,
    new_epoch_hash: str,
):
    """
    Advance the epoch to its next value.

    This function:
    - performs NO constitutional checks
    - performs NO authority checks
    - performs NO registry checks
    - performs NO replay checks

    It assumes all legality has already been enforced
    by the constitutional gateway.

    Runtime admissibility is enforced here.
    """

    # 🔒 RUNTIME TOPOLOGY ENFORCEMENT
    assert_caller_is_constitutional_gateway()

    # Defensive copy / construction
    # The exact mechanics depend on your Epoch model.
    # This implementation assumes an immutable-style constructor.
    try:
        next_epoch = current_epoch.__class__(
            number=current_epoch.number + 1,
            parent=current_epoch.number,
            epoch_hash=new_epoch_hash,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to advance epoch: incompatible epoch model"
        ) from exc

    return next_epoch