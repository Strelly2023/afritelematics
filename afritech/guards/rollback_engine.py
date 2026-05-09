# afritech/guards/rollback_engine.py

"""
AfriTech Rollback Engine

Purpose:
Safely revert state machine to a previous valid state.

Guarantees:
- deterministic rollback behavior
- chain integrity preservation
- no partial or undefined rollback states
- integration with constitutional failure model
"""

from typing import Optional, Dict, Any

from afritech.guards.engine import fail, ViolationClass


# -----------------------------------------------------------------
# ROLLBACK ENGINE
# -----------------------------------------------------------------

class RollbackEngine:

    # -------------------------------------------------------------
    # ROLLBACK LAST TRANSITION
    # -------------------------------------------------------------

    def rollback_last(self, state_engine) -> bool:
        """
        Remove last transition and restore previous state.

        Returns:
            True if rollback succeeded
            False if no rollback possible
        """

        if not state_engine or not hasattr(state_engine, "history"):
            fail(
                "invalid_state_engine",
                ViolationClass.B_STRUCTURAL,
            )

        if not state_engine.history:
            return False  # nothing to rollback

        # Remove last transition
        state_engine.history.pop()

        # Restore state
        if state_engine.history:
            state_engine.current_state = state_engine.history[-1]["to"]
        else:
            state_engine.current_state = "UNINITIALIZED"

        # Reset finalized flag if it exists
        if hasattr(state_engine, "_finalized"):
            state_engine._finalized = (
                state_engine.current_state in ["COMPLETED", "FAILED"]
            )

        return True

    # -------------------------------------------------------------
    # ROLLBACK TO INDEX
    # -------------------------------------------------------------

    def rollback_to(self, state_engine, index: int) -> bool:
        """
        Rollback to a specific transition index.
        """

        if not state_engine or not hasattr(state_engine, "history"):
            fail(
                "invalid_state_engine",
                ViolationClass.B_STRUCTURAL,
            )

        if not isinstance(index, int) or index < 0:
            fail(
                "invalid_rollback_index",
                ViolationClass.B_STRUCTURAL,
            )

        if index >= len(state_engine.history):
            fail(
                "rollback_index_out_of_bounds",
                ViolationClass.B_STRUCTURAL,
            )

        # Trim history
        state_engine.history = state_engine.history[: index + 1]

        # Restore state
        state_engine.current_state = state_engine.history[-1]["to"]

        # Update finalized flag
        if hasattr(state_engine, "_finalized"):
            state_engine._finalized = (
                state_engine.current_state in ["COMPLETED", "FAILED"]
            )

        return True

    # -------------------------------------------------------------
    # FULL RESET (GENESIS STATE)
    # -------------------------------------------------------------

    def reset(self, state_engine) -> bool:
        """
        Reset state engine to initial state.
        """

        if not state_engine:
            fail(
                "invalid_state_engine",
                ViolationClass.B_STRUCTURAL,
            )

        if not hasattr(state_engine, "reset"):
            fail(
                "state_engine_missing_reset",
                ViolationClass.B_STRUCTURAL,
            )

        state_engine.reset()

        return True

    # -------------------------------------------------------------
    # SAFE ROLLBACK ENTRYPOINT (FOR ESCALATION HANDLER)
    # -------------------------------------------------------------

    def execute(
        self,
        state_engine,
        mode: str = "LAST",
        index: Optional[int] = None,
    ) -> bool:
        """
        Unified rollback interface.

        Modes:
            - LAST: rollback last transition
            - INDEX: rollback to specific index
            - RESET: full reset
        """

        if mode == "LAST":
            return self.rollback_last(state_engine)

        elif mode == "INDEX":
            if index is None:
                fail(
                    "missing_index_for_rollback",
                    ViolationClass.B_STRUCTURAL,
                )
            return self.rollback_to(state_engine, index)

        elif mode == "RESET":
            return self.reset(state_engine)

        else:
            fail(
                f"unknown_rollback_mode: {mode}",
                ViolationClass.B_STRUCTURAL,
            )

        return False  # unreachable

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def __repr__(self):
        return "<RollbackEngine deterministic>"