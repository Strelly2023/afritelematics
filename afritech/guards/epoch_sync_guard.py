# afritech/guards/epoch_sync_guard.py

"""
Epoch Synchronization Guard

Purpose:
Ensure consistency between runtime epoch and registry epoch.

Guarantees:
- runtime and registry epochs match exactly
- no drift between execution and recorded history
- deterministic enforcement
- fail-fast on mismatch
"""

from typing import Any, Mapping

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# INTERNAL VALIDATION HELPERS
# -----------------------------------------------------------------

def _validate_runtime_epoch(runtime_epoch: Any):
    if runtime_epoch is None:
        fail("runtime_epoch_missing", ViolationClass.B_STRUCTURAL)

    if not hasattr(runtime_epoch, "id"):
        fail("runtime_epoch_missing_id", ViolationClass.B_STRUCTURAL)

    if not hasattr(runtime_epoch, "version"):
        fail("runtime_epoch_missing_version", ViolationClass.B_STRUCTURAL)


def _validate_registry_epoch(registry_epoch: Any):
    if registry_epoch is None:
        fail("registry_epoch_missing", ViolationClass.B_STRUCTURAL)

    if not isinstance(registry_epoch, Mapping):
        fail("invalid_registry_epoch_structure", ViolationClass.B_STRUCTURAL)

    if "epoch_id" not in registry_epoch:
        fail("registry_epoch_missing_id", ViolationClass.B_STRUCTURAL)

    if "version" not in registry_epoch:
        fail("registry_epoch_missing_version", ViolationClass.B_STRUCTURAL)


# -----------------------------------------------------------------
# MAIN GUARD
# -----------------------------------------------------------------

def enforce_epoch_consistency(
    runtime_epoch,
    registry_epoch,
) -> bool:
    """
    Enforce strict equality between runtime and registry epoch.

    Conditions:
    - id must match
    - version must match

    Failures:
    - fatal → system cannot trust time layer
    """

    # -------------------------------------------------------------
    # STRUCTURAL VALIDATION
    # -------------------------------------------------------------

    _validate_runtime_epoch(runtime_epoch)
    _validate_registry_epoch(registry_epoch)

    runtime_id = runtime_epoch.id
    registry_id = registry_epoch.get("epoch_id")

    runtime_version = runtime_epoch.version
    registry_version = registry_epoch.get("version")

    # -------------------------------------------------------------
    # ID CONSISTENCY
    # -------------------------------------------------------------

    if runtime_id != registry_id:
        fail(
            f"epoch_id_mismatch: runtime={runtime_id}, registry={registry_id}",
            ViolationClass.A_FATAL,
        )

    # -------------------------------------------------------------
    # VERSION CONSISTENCY
    # -------------------------------------------------------------

    if runtime_version != registry_version:
        fail(
            f"epoch_version_mismatch: runtime={runtime_version}, registry={registry_version}",
            ViolationClass.A_FATAL,
        )

    # -------------------------------------------------------------
    # PASS
    # -------------------------------------------------------------

    return True


# -----------------------------------------------------------------
# OPTIONAL EXTENSION (STRICT MODE)
# -----------------------------------------------------------------

def enforce_epoch_strict(
    runtime_epoch,
    registry_epoch,
) -> bool:
    """
    Extended validation enforcing:
    - base consistency
    - sealed state (if present)
    - active state consistency (if present)
    """

    enforce_epoch_consistency(runtime_epoch, registry_epoch)

    # -------------------------------------------------------------
    # OPTIONAL: SEALED VALIDATION
    # -------------------------------------------------------------

    if hasattr(runtime_epoch, "sealed") and "sealed" in registry_epoch:
        if runtime_epoch.sealed != registry_epoch.get("sealed"):
            fail(
                "epoch_sealed_state_mismatch",
                ViolationClass.A_FATAL,
            )

    # -------------------------------------------------------------
    # OPTIONAL: ACTIVE VALIDATION
    # -------------------------------------------------------------

    if hasattr(runtime_epoch, "active") and "active" in registry_epoch:
        if runtime_epoch.active != registry_epoch.get("active"):
            fail(
                "epoch_active_state_mismatch",
                ViolationClass.B_STRUCTURAL,
            )

    return True