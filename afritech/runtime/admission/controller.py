from __future__ import annotations

from typing import Optional

from afritech.contracts.guards_interface import (
    Guard,
    GuardContext,
    GuardResult,
    enforce_guard,
)
from afritech.epoch.epoch_snapshot import EpochSnapshot


# ============================================================
# ✅ Admission Controller (GA-Elite compliant)
# ============================================================

class AdmissionController:
    """
    Sovereign Admission Controller.

    Responsibilities:
    - Gate all execution requests
    - Delegate validation to Guard (via contract)
    - Maintain deterministic admission state

    Architectural Guarantees:
    - No direct dependency on guards.engine
    - Only depends on contracts layer
    - Deterministic and replay-safe
    - Fail-closed behavior
    """

    def __init__(self, guard: Guard) -> None:
        """
        Initialize controller with injected guard.

        Args:
            guard: Implementation of Guard interface
        """
        self._guard: Guard = guard
        self._admitted: bool = False

    # ============================================================
    # ✅ CORE ADMISSION LOGIC
    # ============================================================

    def admit(self, epoch_snapshot: Optional[EpochSnapshot]) -> bool:
        """
        Decide if execution is allowed.

        Flow:
        1. Build deterministic context
        2. Execute guard evaluation
        3. Enforce decision
        4. Set admission state

        Returns:
            True if admitted, False otherwise
        """

        try:
            # ✅ Step 1: Build deterministic context
            context = self._build_context(epoch_snapshot)

            # ✅ Step 2: Evaluate via guard contract
            result: GuardResult = self._guard.evaluate(context)

            # ✅ Step 3: Enforce result (raises if invalid)
            enforce_guard(result)

            # ✅ Step 4: Admission granted
            self._admitted = True
            return True

        except Exception as e:
            # ✅ Step 5: Fail-closed safety
            print(f"❌ Admission denied: {e}")
            self._admitted = False
            return False

    # ============================================================
    # ✅ CONTEXT BUILDER (DETERMINISTIC)
    # ============================================================

    def _build_context(self, epoch_snapshot: Optional[EpochSnapshot]) -> GuardContext:
        """
        Construct deterministic GuardContext.

        Guarantees:
        - Replay-safe
        - No non-deterministic values
        - Fully serializable
        """

        if epoch_snapshot is None:
            return GuardContext(
                request_id="unknown",
                timestamp=0,
                actor_id=None,
                surface="runtime.admission",
                action="admit",
                payload_hash="none",
                metadata={
                    "epoch": None,
                    "state": None,
                },
            )

        return GuardContext(
            request_id=str(getattr(epoch_snapshot, "epoch_id", "unknown")),
            timestamp=int(getattr(epoch_snapshot, "timestamp", 0) or 0),
            actor_id=getattr(epoch_snapshot, "authority", None),
            surface="runtime.admission",
            action="admit",
            payload_hash=str(getattr(epoch_snapshot, "hash", "none")),
            metadata={
                "epoch": getattr(epoch_snapshot, "epoch_id", None),
                "state": getattr(epoch_snapshot, "state", None),
                "epoch_snapshot": epoch_snapshot,
            },
        )

    # ============================================================
    # ✅ STATE MANAGEMENT
    # ============================================================

    def reset(self) -> None:
        """
        Reset admission state.

        Use cases:
        - Testing
        - Replay cycles
        - Multi-execution flows
        """
        self._admitted = False

    def is_admitted(self) -> bool:
        """
        Check admission status.
        """
        return self._admitted

    # ============================================================
    # ✅ UTILITIES
    # ============================================================

    def __bool__(self) -> bool:
        return self._admitted

    def __repr__(self) -> str:
        return f"<AdmissionController admitted={self._admitted}>"

    # ============================================================
    # ✅ FACTORY (OPTIONAL HELPER)
    # ============================================================

    @classmethod
    def create(cls, guard: Guard) -> "AdmissionController":
        """
        Factory method for explicit construction.
        """
        return cls(guard)


# ============================================================
# ✅ EXPORT
# ============================================================

__all__ = [
    "AdmissionController",
]
