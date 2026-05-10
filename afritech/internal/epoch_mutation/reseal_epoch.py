# afritech/internal/epoch_mutation/reseal_epoch.py

"""
AfriTech Internal Epoch Reseal
==============================

This module contains mutation-capable logic for resealing
an epoch after lawful advancement.

CRITICAL CONSTITUTIONAL RULES:
- This module MUST NOT be imported outside the constitutional gateway
- This module MUST enforce runtime admissibility
- This module MUST NOT enforce constitutional law
- This module MUST NOT infer authority, ADRs, or policy
- This module MUST perform only reseal mechanics

All reseal legality (ADR presence, epoch validity, monotonicity,
registry authority, replay constraints, etc.) MUST already have been
enforced by the constitutional gateway.
"""

from __future__ import annotations

from afritech.internal.admissibility import assert_caller_is_constitutional_gateway


# ---------------------------------------------------------------------
# EPOCH RESEAL (MUTATION-CAPABLE)
# ---------------------------------------------------------------------

def reseal_epoch(
    epoch_obj,
    *,
    reseal_hash: str,
):
    """
    Reseal an epoch object with a new cryptographic hash.

    This function:
    - performs NO constitutional validation
    - performs NO authority checks
    - performs NO epoch legality checks
    - performs NO registry checks
    - assumes all legality has already been enforced

    Runtime admissibility is enforced here.
    """

    # 🔒 RUNTIME TOPOLOGY ENFORCEMENT
    assert_caller_is_constitutional_gateway()

    # Defensive reconstruction
    # Assumes epoch_obj exposes resealable fields and constructor
    try:
        resealed_epoch = epoch_obj.__class__(
            number=epoch_obj.number,
            parent=epoch_obj.parent,
            epoch_hash=reseal_hash,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to reseal epoch: incompatible epoch model"
        ) from exc

    return resealed_epoch