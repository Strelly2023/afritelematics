# afritech/epoch/epoch_transition.py

"""
AfriTech Epoch Transition Rules

Purpose:
Define and enforce valid transitions between epochs.

Guarantees:
- strictly monotonic time progression
- no reuse of instance_id
- sealed history enforcement
- deterministic transition validation
"""

from __future__ import annotations

from afritech.epoch.epoch import Epoch
from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# CORE TRANSITION VALIDATION
# -----------------------------------------------------------------

def validate_epoch_transition(prev: Epoch, next_epoch: Epoch) -> bool:
    """
    Validate transition from prev → next_epoch

    Rules:
    - prev MUST be sealed
    - version MUST strictly increase
    - instance_id MUST change
    - next_epoch MUST be valid structurally
    """

    # -------------------------------------------------------------
    # STRUCTURAL CHECKS
    # -------------------------------------------------------------

    if not isinstance(prev, Epoch):
        fail(
            "invalid_previous_epoch",
            ViolationClass.B_STRUCTURAL,
        )

    if not isinstance(next_epoch, Epoch):
        fail(
            "invalid_next_epoch",
            ViolationClass.B_STRUCTURAL,
        )

    # -------------------------------------------------------------
    # PREVIOUS EPOCH MUST BE SEALED
    # -------------------------------------------------------------

    if not prev.sealed:
        fail(
            "previous_epoch_not_sealed",
            ViolationClass.A_FATAL,
        )

    # -------------------------------------------------------------
    # STRICT VERSION MONOTONICITY
    # -------------------------------------------------------------

    if next_epoch.version <= prev.version:
        fail(
            f"invalid_epoch_version_progression: prev={prev.version}, next={next_epoch.version}",
            ViolationClass.A_FATAL,
        )

    # -------------------------------------------------------------
    # INSTANCE ID MUST CHANGE
    # -------------------------------------------------------------

    if next_epoch.instance_id == prev.instance_id:
        fail(
            "epoch_instance_reuse_forbidden",
            ViolationClass.B_STRUCTURAL,
        )

    # -------------------------------------------------------------
    # ID CONSISTENCY (OPTIONAL POLICY)
    # -------------------------------------------------------------

    if not next_epoch.id:
        fail(
            "next_epoch_missing_id",
            ViolationClass.B_STRUCTURAL,
        )

    # -------------------------------------------------------------
    # CANNOT ACTIVATE SEALED NEXT EPOCH
    # -------------------------------------------------------------

    if next_epoch.sealed and next_epoch.active:
        fail(
            "sealed_epoch_cannot_be_active",
            ViolationClass.B_STRUCTURAL,
        )

    # -------------------------------------------------------------
    # PASS
    # -------------------------------------------------------------

    return True


# -----------------------------------------------------------------
# EXTENDED TRANSITION VALIDATION (STRICT MODE)
# -----------------------------------------------------------------

def validate_epoch_transition_strict(prev: Epoch, next_epoch: Epoch) -> bool:
    """
    Extended validation with additional invariants.

    Adds:
    - id continuity (optional policy)
    - active flag enforcement
    """

    validate_epoch_transition(prev, next_epoch)

    # -------------------------------------------------------------
    # OPTIONAL: ID CONTINUITY POLICY
    # (depends on your governance model)
    # -------------------------------------------------------------

    if prev.id == next_epoch.id:
        # allow same logical id (version evolves)
        pass
    else:
        # optional restriction (comment out if not needed)
        # fail("epoch_id_change_not_allowed", ViolationClass.B_STRUCTURAL)
        pass

    # -------------------------------------------------------------
    # ACTIVE FLAG RULE
    # -------------------------------------------------------------

    if not next_epoch.active:
        fail(
            "next_epoch_must_be_active",
            ViolationClass.B_STRUCTURAL,
        )

    return True


# -----------------------------------------------------------------
# SAFE TRANSITION EXECUTION
# -----------------------------------------------------------------

def transition_epoch(prev: Epoch, next_epoch: Epoch) -> Epoch:
    """
    Validate and return next epoch.

    Used as functional helper (side-effect free).
    """

    validate_epoch_transition(prev, next_epoch)

    return next_epoch


# -----------------------------------------------------------------
# DEBUG / TRACE HELPERS
# -----------------------------------------------------------------

def describe_transition(prev: Epoch, next_epoch: Epoch) -> str:
    """
    Provides human-readable transition description.
    """

    return (
        f"EpochTransition("
        f"{prev.id}@v{prev.version} -> "
        f"{next_epoch.id}@v{next_epoch.version})"
    )