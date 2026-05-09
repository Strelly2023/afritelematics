# afritech/epoch/epoch_manager.py

"""
AfriTech Epoch Manager

Purpose:
Control lifecycle and transitions of system epochs.

Guarantees:
- single active epoch
- deterministic time progression
- strict monotonic versioning
- sealed history enforcement
- no invalid transitions
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from afritech.epoch.epoch import Epoch
from afritech.epoch.epoch_validator import EpochValidator
from afritech.epoch.epoch_transition import validate_epoch_transition
from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# EPOCH MANAGER
# -----------------------------------------------------------------

class EpochManager:

    def __init__(self):
        self._current_epoch: Optional[Epoch] = None
        self._history: list[Epoch] = []

    # -------------------------------------------------------------
    # INITIALIZATION
    # -------------------------------------------------------------

    def initialize(self, epoch: Epoch) -> None:
        """
        Set initial epoch (genesis time).
        Can only be called once.
        """

        if self._current_epoch is not None:
            fail(
                "epoch_already_initialized",
                ViolationClass.B_STRUCTURAL,
            )

        EpochValidator.validate(epoch)

        self._current_epoch = epoch
        self._history.append(epoch)

    # -------------------------------------------------------------
    # CURRENT EPOCH
    # -------------------------------------------------------------

    def current(self) -> Epoch:
        """
        Return active epoch.
        """

        if not self._current_epoch:
            fail("no_active_epoch", ViolationClass.A_FATAL)

        return self._current_epoch

    # -------------------------------------------------------------
    # TRANSITION
    # -------------------------------------------------------------

    def transition(self, next_epoch: Epoch) -> Epoch:
        """
        Transition to a new epoch.

        Rules:
        - must have current epoch
        - current must be sealed
        - version must increase
        - instance_id must change
        """

        if not self._current_epoch:
            fail(
                "cannot_transition_without_current_epoch",
                ViolationClass.A_FATAL,
            )

        current = self._current_epoch

        # Validate both epochs structurally
        EpochValidator.validate(next_epoch)

        # Validate transition logic
        validate_epoch_transition(current, next_epoch)

        # Enforce current epoch is sealed
        if not current.sealed:
            fail(
                "current_epoch_not_sealed",
                ViolationClass.A_FATAL,
            )

        # Apply transition
        self._current_epoch = next_epoch
        self._history.append(next_epoch)

        return next_epoch

    # -------------------------------------------------------------
    # SEAL CURRENT EPOCH
    # -------------------------------------------------------------

    def seal_current(self) -> Epoch:
        """
        Seal the current epoch (make immutable).
        """

        if not self._current_epoch:
            fail("no_active_epoch", ViolationClass.A_FATAL)

        sealed_epoch = self._current_epoch.seal()

        # Replace current with sealed version
        self._current_epoch = sealed_epoch
        self._history[-1] = sealed_epoch

        return sealed_epoch

    # -------------------------------------------------------------
    # HISTORY ACCESS
    # -------------------------------------------------------------

    def history(self) -> list[Epoch]:
        """
        Return immutable snapshot of epoch history.
        """

        return list(self._history)

    # -------------------------------------------------------------
    # GET BY VERSION
    # -------------------------------------------------------------

    def get_by_version(self, version: int) -> Optional[Epoch]:
        """
        Retrieve epoch by version.
        """

        for epoch in self._history:
            if epoch.version == version:
                return epoch

        return None

    # -------------------------------------------------------------
    # CONSISTENCY CHECK
    # -------------------------------------------------------------

    def validate_monotonicity(self) -> bool:
        """
        Ensure epoch versions strictly increase.
        """

        for i in range(1, len(self._history)):
            if self._history[i].version <= self._history[i - 1].version:
                fail(
                    "epoch_history_not_monotonic",
                    ViolationClass.A_FATAL,
                )

        return True

    # -------------------------------------------------------------
    # EXPORT (REGISTRY SYNC)
    # -------------------------------------------------------------

    def export_current(self) -> Dict[str, Any]:
        """
        Export current epoch to registry-compatible format.
        """

        epoch = self.current()

        return epoch.to_dict()

    # -------------------------------------------------------------
    # RELOAD FROM REGISTRY
    # -------------------------------------------------------------

    def load_from_registry(self, record: Dict[str, Any]) -> Epoch:
        """
        Load epoch from registry record.

        Ensures deterministic reconstruction.
        """

        if not isinstance(record, dict):
            fail(
                "invalid_registry_epoch_record",
                ViolationClass.B_STRUCTURAL,
            )

        required = ["epoch_id", "instance_id", "version", "active", "sealed"]

        for field in required:
            if field not in record:
                fail(
                    f"missing_registry_field:{field}",
                    ViolationClass.B_STRUCTURAL,
                )

        epoch = Epoch.create(
            id=record["epoch_id"],
            instance_id=record["instance_id"],
            version=record["version"],
            active=record["active"],
            sealed=record["sealed"],
        )

        return epoch

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return (
            f"<EpochManager current={self._current_epoch} "
            f"history_len={len(self._history)}>"
        )