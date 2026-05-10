"""
AfriTech Epoch Manager

Purpose:
Authoritative controller for epoch lifecycle and temporal legitimacy.

Constitutional Guarantees:
- single active epoch authority
- deterministic epoch progression
- strict monotonic versioning
- sealed-history enforcement
- parent continuity
- genesis legality
- anti-fork protection

PHASE-1 STATUS:
This module enforces runtime epoch constitutional constraints.

Formal discharge is delegated to:

    afritech/proof/formal/generate_epoch_lean.py
    afritech/proof/formal/check_epoch_proofs.py
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from afritech.epoch.compiled.semantic_epoch import SemanticEpoch, EpochType
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.guards.engine import fail, ViolationClass

from afritech.constitution.compiled.invariants_index import (
    I13_EPOCH_MONOTONIC,
)

# ---------------------------------------------------------------------
# CONSTITUTIONAL INVARIANT DECLARATION
# ---------------------------------------------------------------------

ENFORCED_INVARIANTS = {
    I13_EPOCH_MONOTONIC,
}

# ---------------------------------------------------------------------
# GLOBAL EPOCH AUTHORITY REGISTRATION
# ---------------------------------------------------------------------

_ACTIVE_MANAGER: Optional["EpochManager"] = None


# ---------------------------------------------------------------------
# EPOCH MANAGER
# ---------------------------------------------------------------------

class EpochManager:
    """
    Authoritative epoch lifecycle controller.

    Guarantees:
        - singleton authority
        - temporal continuity
        - monotonic advancement
        - replay-safe history
    """

    def __init__(self):
        global _ACTIVE_MANAGER

        if _ACTIVE_MANAGER is not None:
            fail(
                "duplicate_epoch_manager_authority",
                ViolationClass.B_STRUCTURAL,
            )

        _ACTIVE_MANAGER = self

        self._current_epoch: Optional[EpochSnapshot] = None
        self._history: List[EpochSnapshot] = []
        self._epoch_hashes = set()

    # -----------------------------------------------------------------
    # INITIALIZATION
    # -----------------------------------------------------------------

    def initialize(self, epoch: EpochSnapshot) -> None:
        """
        Initialize epoch authority.

        Constitutional rules:
        - may only occur once
        - must be genesis epoch
        """

        if self._current_epoch is not None:
            fail(
                "epoch_already_initialized",
                ViolationClass.B_STRUCTURAL,
            )

        self._validate_epoch_snapshot(epoch)
        self._validate_genesis(epoch)

        self._current_epoch = epoch
        self._history.append(epoch)
        self._epoch_hashes.add(epoch.epoch_hash)

    # -----------------------------------------------------------------
    # CURRENT EPOCH
    # -----------------------------------------------------------------

    def current(self) -> EpochSnapshot:
        """
        Return active epoch.
        """

        if self._current_epoch is None:
            fail(
                "no_active_epoch",
                ViolationClass.A_FATAL,
            )

        return self._current_epoch

    # -----------------------------------------------------------------
    # TRANSITION
    # -----------------------------------------------------------------

    def transition(self, next_epoch: EpochSnapshot) -> EpochSnapshot:
        """
        Transition to next epoch.

        Constitutional rules:
        - current epoch required
        - current must be sealed
        - strict monotonic progression
        - parent continuity required
        - no epoch reuse
        """

        if self._current_epoch is None:
            fail(
                "cannot_transition_without_current_epoch",
                ViolationClass.A_FATAL,
            )

        self._validate_epoch_snapshot(next_epoch)

        current = self._current_epoch

        # -------------------------------------------------------------
        # I13 — STRICT MONOTONICITY
        # -------------------------------------------------------------

        if next_epoch.semantic_epoch.number <= current.semantic_epoch.number:
            fail(
                "epoch_monotonicity_violation",
                ViolationClass.A_FATAL,
            )

        # -------------------------------------------------------------
        # SEALED HISTORY
        # -------------------------------------------------------------

        if not current.semantic_epoch.sealed:
            fail(
                "current_epoch_not_sealed",
                ViolationClass.A_FATAL,
            )

        # -------------------------------------------------------------
        # PARENT CONTINUITY
        # -------------------------------------------------------------

        if next_epoch.parent_hash != current.epoch_hash:
            fail(
                "epoch_parent_continuity_violation",
                ViolationClass.A_FATAL,
            )

        # -------------------------------------------------------------
        # ANTI-FORK / REUSE
        # -------------------------------------------------------------

        if next_epoch.epoch_hash in self._epoch_hashes:
            fail(
                "epoch_reuse_detected",
                ViolationClass.A_FATAL,
            )

        self._current_epoch = next_epoch
        self._history.append(next_epoch)
        self._epoch_hashes.add(next_epoch.epoch_hash)

        return next_epoch

    # -----------------------------------------------------------------
    # HISTORY
    # -----------------------------------------------------------------

    def history(self) -> List[EpochSnapshot]:
        """
        Return immutable epoch history.
        """

        return list(self._history)

    # -----------------------------------------------------------------
    # CONSISTENCY CHECKS
    # -----------------------------------------------------------------

    def validate_monotonicity(self) -> bool:
        """
        Verify strictly increasing epoch sequence.
        """

        for i in range(1, len(self._history)):
            prev = self._history[i - 1]
            curr = self._history[i]

            if curr.semantic_epoch.number <= prev.semantic_epoch.number:
                fail(
                    "epoch_history_not_monotonic",
                    ViolationClass.A_FATAL,
                )

        return True

    def validate_parent_chain(self) -> bool:
        """
        Verify epoch lineage continuity.
        """

        for i in range(1, len(self._history)):
            prev = self._history[i - 1]
            curr = self._history[i]

            if curr.parent_hash != prev.epoch_hash:
                fail(
                    "epoch_history_parent_break",
                    ViolationClass.A_FATAL,
                )

        return True

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def export_current(self) -> Dict[str, Any]:
        """
        Export current epoch to registry-compatible format.
        """

        epoch = self.current()

        return {
            "epoch_number": epoch.semantic_epoch.number,
            "epoch_type": epoch.semantic_epoch.epoch_type.name,
            "sealed": epoch.semantic_epoch.sealed,
            "epoch_hash": epoch.epoch_hash,
            "parent_hash": epoch.parent_hash,
        }

    # -----------------------------------------------------------------
    # INTERNAL VALIDATION
    # -----------------------------------------------------------------

    @staticmethod
    def _validate_epoch_snapshot(epoch: EpochSnapshot) -> None:
        """
        Structural epoch validation.
        """

        if not isinstance(epoch, EpochSnapshot):
            fail(
                "invalid_epoch_snapshot_type",
                ViolationClass.B_STRUCTURAL,
            )

        semantic = epoch.semantic_epoch

        if not isinstance(semantic, SemanticEpoch):
            fail(
                "epoch_missing_compiled_semantics",
                ViolationClass.B_STRUCTURAL,
            )

        if not isinstance(semantic.number, int):
            fail(
                "epoch_number_not_int",
                ViolationClass.B_STRUCTURAL,
            )

    @staticmethod
    def _validate_genesis(epoch: EpochSnapshot) -> None:
        """
        Validate genesis legality.
        """

        semantic = epoch.semantic_epoch

        if semantic.number != 0:
            fail(
                "invalid_genesis_epoch_number",
                ViolationClass.A_FATAL,
            )

        if semantic.epoch_type != EpochType.GENESIS:
            fail(
                "invalid_genesis_epoch_type",
                ViolationClass.A_FATAL,
            )

    # -----------------------------------------------------------------
    # AUTHORITY RELEASE
    # -----------------------------------------------------------------

    @staticmethod
    def release_authority() -> None:
        """
        Release singleton authority.

        Intended for controlled testing only.
        """

        global _ACTIVE_MANAGER
        _ACTIVE_MANAGER = None

    # -----------------------------------------------------------------
    # DEBUG
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<EpochManager "
            f"current={self._current_epoch} "
            f"history_len={len(self._history)}>"
        )