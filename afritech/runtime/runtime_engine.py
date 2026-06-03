from __future__ import annotations

from typing import Callable, Any, Optional, List, Dict

from afritech.epoch.epoch_snapshot import EpochSnapshot

from afritech.runtime.admission.controller import AdmissionController
from afritech.runtime.kernel.execute import ExecutionKernel, ExecutionContext
from afritech.runtime.audit.ledger import AuditLedger

from afritech.guards.engine import verify_sovereignty


# ---------------------------------------------------------
# Runtime Engine (Sovereign Orchestrator)
# ---------------------------------------------------------

class RuntimeEngine:
    """
    GA Elite Sovereign Runtime Engine

    Responsibilities:
    - Central orchestration of execution lifecycle
    - Ensures sovereignty before execution
    - Maintains kernel + admission + audit state
    - Provides reusable execution interface
    """

    def __init__(self) -> None:
        # ✅ Persistent components (NO re-instantiation per call)
        self._admission = AdmissionController()
        self._kernel = ExecutionKernel(self._admission)
        self._ledger = AuditLedger()

        # ✅ Runtime state
        self._initialized: bool = False
        self._last_epoch: Optional[EpochSnapshot] = None

    # -----------------------------------------------------
    # Initialization
    # -----------------------------------------------------

    def initialize(self, epoch_snapshot: EpochSnapshot) -> None:
        """
        Initialize runtime with a valid epoch.

        Performs:
        - Sovereignty validation
        - Admission gating
        """

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("RuntimeEngine requires a valid EpochSnapshot")

        # ✅ Sovereignty validation (global pre-check)
        verify_sovereignty(epoch_snapshot)

        # ✅ Admission
        admitted = self._admission.admit(epoch_snapshot)
        if not admitted:
            raise RuntimeError("Runtime initialization failed: admission denied")

        self._initialized = True
        self._last_epoch = epoch_snapshot

    # -----------------------------------------------------
    # Execution (Primary API)
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: Optional[EpochSnapshot] = None,
    ) -> Any:
        """
        Execute a function under sovereign control.

        Guarantees:
        - Admission validated
        - Kernel-enforced execution
        - Deterministic boundary
        - Audit logging
        """

        # ✅ Ensure runtime initialized
        if not self._initialized:
            if epoch_snapshot is None:
                raise RuntimeError("RuntimeEngine not initialized and no epoch provided")
            self.initialize(epoch_snapshot)

        # ✅ Optional epoch override (controlled)
        if epoch_snapshot is not None:
            self._validate_epoch_transition(epoch_snapshot)
            self._last_epoch = epoch_snapshot

        assert self._last_epoch is not None  # Pylance safety

        # ✅ Build execution context
        context = ExecutionContext(self._last_epoch)

        # ✅ Execute via sovereign kernel
        result = self._kernel.execute(fn, context)

        # ✅ Record audit
        self._ledger.record(fn.__name__, result, context)

        return result

    # -----------------------------------------------------
    # Batch execution (Advanced)
    # -----------------------------------------------------

    def execute_batch(
        self,
        functions: List[Callable[[ExecutionContext], Any]],
        epoch_snapshot: Optional[EpochSnapshot] = None,
    ) -> List[Any]:
        """
        Execute multiple functions sequentially under same context.
        """

        results: List[Any] = []

        for fn in functions:
            result = self.execute(fn, epoch_snapshot)
            results.append(result)

        return results

    # -----------------------------------------------------
    # Audit access
    # -----------------------------------------------------

    def get_audit_records(self) -> List[Dict[str, Any]]:
        """
        Retrieve all execution logs.
        """
        return self._ledger.get_records()

    def clear_audit(self) -> None:
        """
        Clear audit ledger (testing only).
        """
        self._ledger.clear()

    # -----------------------------------------------------
    # Internal validation
    # -----------------------------------------------------

    def _validate_epoch_transition(self, epoch_snapshot: EpochSnapshot) -> None:
        """
        Ensure safe epoch transitions.
        """

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid epoch transition")

        if self._last_epoch is None:
            return

        current = self._last_epoch.semantic_epoch.number
        incoming = epoch_snapshot.semantic_epoch.number

        # ✅ Basic monotonic enforcement (can extend later)
        if incoming < current:
            raise RuntimeError(
                f"Invalid epoch transition: {incoming} < {current}"
            )

    # -----------------------------------------------------
    # Status / inspection
    # -----------------------------------------------------

    def is_initialized(self) -> bool:
        return self._initialized

    def get_current_epoch(self) -> Optional[int]:
        if self._last_epoch:
            return self._last_epoch.semantic_epoch.number
        return None

    def reset(self) -> None:
        """
        Full runtime reset.
        """

        self._admission.reset()
        self._ledger.clear()

        self._initialized = False
        self._last_epoch = None
