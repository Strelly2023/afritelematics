from __future__ import annotations

from typing import Optional

from afritech.contracts.guards_interface import (
    Guard,
    GuardContext,
    GuardExecutionError,
    enforce_guard,
)
from afritech.epoch.epoch_snapshot import EpochSnapshot
# afritech/runtime/admission/controller.py

class AdmissionController:
    """
    Sovereign Admission Controller (GA Elite compliant).

    Responsibilities:
    - Gate all execution requests
    - Delegate validation to guards (contract-based)
    - Maintain deterministic admission state

    Architectural Rules:
    - MUST NOT import guards.engine directly
    - MUST depend only on contracts interface
    - MUST remain deterministic and replay-safe
    """

    def __init__(self, guard: Guard) -> None:
        """
        Initialize controller with injected guard.

        Dependency injection removes circular imports.

        Args:
            guard: Guard implementation (from afritech.guards.engine)
        """
        self._guard: Guard = guard
        self._admitted: bool = False

    # ============================================================
    # CORE ADMISSION LOGIC
    # ============================================================

    def admit(self, epoch_snapshot: Optional[EpochSnapshot]) -> bool:
        """
        Decide if execution is allowed.

        Behavior:
        - Builds deterministic GuardContext
        - Delegates decision to guard
        - Enforces result safely
        - Never crashes (fail-safe)

        Returns:
            bool: admission decision
        """

        try:
            # ✅ Step 1: Construct deterministic context
            context = self._build_context(epoch_snapshot)

            # ✅ Step 2: Delegate to guard (NO direct sovereignty import)
            result = self._guard.evaluate(context)

            # ✅ Step 3: Enforce decision
            enforce_guard(result)

            # ✅ Step 4: Admission success
            self._admitted = True
            return True

        except Exception as e:
            # ✅ Step 5: Safe failure (fail-closed)
            print(f"❌ Admission denied: {e}")
            self._admitted = False
            return False

    # ============================================================
    # CONTEXT CONSTRUCTION
    # ============================================================

    def _build_context(self, epoch_snapshot: Optional[EpochSnapshot]) -> GuardContext:
        """
        Build a deterministic GuardContext from epoch snapshot.

        MUST NOT:
        - include non-deterministic values
        - depend on runtime state outside snapshot

        Returns:
            GuardContext
        """

        # Safe defaults for replay
        if epoch_snapshot is None:
            return GuardContext(
                request_id="unknown",
                timestamp=0,
                actor_id=None,
                surface="runtime.admission",
                action="admit",
                payload_hash="none",
                metadata={"epoch": None},
            )

        return GuardContext(
            request_id=str(epoch_snapshot.epoch_id),
            timestamp=int(epoch_snapshot.timestamp),
            actor_id=getattr(epoch_snapshot, "authority", None),
            surface="runtime.admission",
            action="admit",
            payload_hash=str(epoch_snapshot.hash),
            metadata={
                "epoch": epoch_snapshot.epoch_id,
                "state": getattr(epoch_snapshot, "state", None),
            },
        )

    # ============================================================
    # STATE MANAGEMENT
    # ============================================================

    def reset(self) -> None:
        """
        Reset admission state.

        Useful for:
        - testing
        - multi-run isolation
        - replay reset
        """
        self._admitted = False

    def is_admitted(self) -> bool:
        """
        Check admission status.

        Returns:
            bool
        """
        return self._admitted


__all__ = [
    "AdmissionController",
]