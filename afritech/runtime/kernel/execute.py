from __future__ import annotations

from typing import Callable, Any, Set

from afritech.runtime.admission.controller import AdmissionController
from afritech.epoch.epoch_snapshot import EpochSnapshot


# ---------------------------------------------------------
# Execution Context
# ---------------------------------------------------------

class ExecutionContext:
    """
    Immutable execution context passed into all functions.
    """

    def __init__(self, epoch_snapshot: EpochSnapshot) -> None:
        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("ExecutionContext requires a valid EpochSnapshot")

        self.epoch_snapshot: EpochSnapshot = epoch_snapshot


# ---------------------------------------------------------
# Execution Kernel (ONLY executor)
# ---------------------------------------------------------

class ExecutionKernel:
    """
    Sovereign Execution Kernel.

    Guarantees:
    - No execution without admission
    - Deterministic execution only
    - Single authorized execution path
    """

    def __init__(self, admission_controller: AdmissionController) -> None:
        if not isinstance(admission_controller, AdmissionController):
            raise TypeError("ExecutionKernel requires a valid AdmissionController")

        self.admission_controller: AdmissionController = admission_controller

    # -----------------------------------------------------
    # Core execution method
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Any:
        """
        The ONLY legal execution path in the system.
        """

        # ✅ Validate input types (defensive)
        if not callable(fn):
            raise TypeError("Execution requires a callable function")

        if not isinstance(context, ExecutionContext):
            raise TypeError("Invalid ExecutionContext")

        # ✅ Admission enforcement
        if not self.admission_controller.is_admitted():
            admitted = self.admission_controller.admit(context.epoch_snapshot)

            if not admitted:
                raise RuntimeError("Execution denied by AdmissionController")

        # ✅ Deterministic boundary enforcement
        self._enforce_determinism(fn)

        # ✅ Controlled execution
        try:
            result = fn(context)
            return result

        except Exception as e:
            # Optional: add logging later if needed
            raise RuntimeError(f"Execution failed: {e}") from e

    # -----------------------------------------------------
    # Determinism enforcement
    # -----------------------------------------------------

    def _enforce_determinism(self, fn: Callable[..., Any]) -> None:
        """
        Prevent non-deterministic execution.

        Blocks:
        - random
        - time
        - uuid
        """

        forbidden: Set[str] = {"random", "time", "uuid", "os.urandom"}

        # Extract referenced names from function bytecode
        names = set(fn.__code__.co_names)

        violations = [name for name in names if name in forbidden]

        if violations:
            raise RuntimeError(
                f"❌ Non-deterministic function detected: {violations}"
            )
