# afritech/epoch/epoch_validator.py

"""
AfriTech Epoch Validator

Purpose:
Validate structural and logical correctness of Epoch objects.

Guarantees:
- no malformed epoch objects
- deterministic validation
- compatibility with registry + guards
- fail-fast enforcement

All failures delegate to engine.fail()
"""

from __future__ import annotations

from afritech.epoch.epoch import Epoch
from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# VALIDATOR
# -----------------------------------------------------------------

class EpochValidator:

    # -------------------------------------------------------------
    # ENTRYPOINT
    # -------------------------------------------------------------

    @staticmethod
    def validate(epoch: Epoch) -> bool:
        """
        Validate a single epoch instance.

        Checks:
        - structure
        - types
        - logical consistency
        """

        # ---------------------------------------------------------
        # TYPE CHECK
        # ---------------------------------------------------------

        if not isinstance(epoch, Epoch):
            fail(
                "invalid_epoch_object",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # ID VALIDATION
        # ---------------------------------------------------------

        if not isinstance(epoch.id, str) or not epoch.id.strip():
            fail(
                "invalid_epoch_id",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # INSTANCE ID VALIDATION
        # ---------------------------------------------------------

        if not isinstance(epoch.instance_id, str) or not epoch.instance_id.strip():
            fail(
                "invalid_epoch_instance_id",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # VERSION VALIDATION
        # ---------------------------------------------------------

        if not isinstance(epoch.version, int):
            fail(
                "epoch_version_not_int",
                ViolationClass.B_STRUCTURAL,
            )

        if epoch.version < 0:
            fail(
                "negative_epoch_version",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # FLAGS VALIDATION
        # ---------------------------------------------------------

        if not isinstance(epoch.active, bool):
            fail(
                "invalid_epoch_active_flag",
                ViolationClass.B_STRUCTURAL,
            )

        if not isinstance(epoch.sealed, bool):
            fail(
                "invalid_epoch_sealed_flag",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # LOGICAL CONSISTENCY
        # ---------------------------------------------------------

        # ❌ sealed + active is inconsistent
        if epoch.sealed and epoch.active:
            fail(
                "sealed_epoch_cannot_be_active",
                ViolationClass.B_STRUCTURAL,
            )

        # ✅ version 0 must be initial epoch (optional policy)
        if epoch.version == 0 and not epoch.instance_id:
            fail(
                "genesis_epoch_missing_instance_id",
                ViolationClass.B_STRUCTURAL,
            )

        # ---------------------------------------------------------
        # PASS
        # ---------------------------------------------------------

        return True

    # -------------------------------------------------------------
    # SAFE VALIDATION
    # -------------------------------------------------------------

    @classmethod
    def try_validate(cls, epoch: Epoch) -> bool:
        """
        Safe validation wrapper (no crash).
        """

        try:
            return cls.validate(epoch)
        except SystemExit:
            return False

    # -------------------------------------------------------------
    # BATCH VALIDATION
    # -------------------------------------------------------------

    @classmethod
    def validate_sequence(cls, epochs: list[Epoch]) -> bool:
        """
        Validate a sequence of epochs.

        Enforces:
        - all epochs valid
        - monotonic version progression
        """

        if not isinstance(epochs, list):
            fail(
                "invalid_epoch_sequence",
                ViolationClass.B_STRUCTURAL,
            )

        if not epochs:
            fail(
                "empty_epoch_sequence",
                ViolationClass.A_FATAL,
            )

        for epoch in epochs:
            cls.validate(epoch)

        # ---------------------------------------------------------
        # MONOTONICITY CHECK
        # ---------------------------------------------------------

        for i in range(1, len(epochs)):
            if epochs[i].version <= epochs[i - 1].version:
                fail(
                    "epoch_sequence_not_monotonic",
                    ViolationClass.A_FATAL,
                )

        return True

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return "<EpochValidator strict>"