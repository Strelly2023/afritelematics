from __future__ import annotations

from typing import Callable, Any, Optional, List, Dict

from afritech.epoch.epoch_snapshot import EpochSnapshot

from afritech.runtime.admission.controller import AdmissionController
from afritech.runtime.kernel.execute import ExecutionKernel, ExecutionContext
from afritech.runtime.audit.ledger import AuditLedger

from afritech.guards.engine import verify_sovereignty, SovereigntyGuard


class RuntimeEngine:
    """
    🔥 GA-Elite Sovereign Runtime Engine

    Guarantees:
    - Deterministic execution
    - Admission-controlled execution
    - Replay-safe audit logging
    - Distributed consistency
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self) -> None:
        self._guard = SovereigntyGuard()
        self._admission = AdmissionController(self._guard)

        self._kernel = ExecutionKernel(self._admission)
        self._ledger = AuditLedger()

        self._initialized: bool = False
        self._last_epoch: Optional[EpochSnapshot] = None

    # =====================================================
    # ✅ INITIALIZATION
    # =====================================================

    def initialize(self, epoch_snapshot: EpochSnapshot) -> None:

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("RuntimeEngine requires a valid EpochSnapshot")

        verify_sovereignty(epoch_snapshot)

        admitted = self._admission.admit(epoch_snapshot)
        if not admitted:
            raise RuntimeError("Runtime initialization failed: admission denied")

        self._initialized = True
        self._last_epoch = epoch_snapshot

    # =====================================================
    # ✅ EXECUTION (UPGRADED)
    # =====================================================

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: Optional[EpochSnapshot] = None,
        fn_id: Optional[str] = None,   # ✅ NEW
    ) -> Any:

        if not callable(fn):
            raise TypeError("fn must be callable")

        # ✅ init bootstrap
        if not self._initialized:
            if epoch_snapshot is None:
                raise RuntimeError("RuntimeEngine not initialized and no epoch provided")
            self.initialize(epoch_snapshot)

        # ✅ epoch override
        if epoch_snapshot is not None:
            self._validate_epoch_transition(epoch_snapshot)
            self._last_epoch = epoch_snapshot

        assert self._last_epoch is not None

        # ✅ deterministic execution context
        context = ExecutionContext(self._last_epoch)

        # ✅ execution
        result = self._kernel.execute(fn, context)

        # ✅ deterministic execution id
        execution_id = fn_id if isinstance(fn_id, str) else self._safe_fn_id(fn)

        # ✅ audit logging (UPGRADED)
        self._ledger.record(
            execution_id,
            result,
            context,
        )

        return result

    # =====================================================
    # ✅ SAFE FUNCTION ID (CRITICAL)
    # =====================================================

    def _safe_fn_id(self, fn: Callable) -> str:
        """
        Generate deterministic fallback function identifier.
        """

        try:
            name = getattr(fn, "__name__", "anonymous")

            module = getattr(fn, "__module__", "unknown")

            return f"{module}.{name}"
        except Exception:
            return "unknown.execution"

    # =====================================================
    # ✅ BATCH EXECUTION
    # =====================================================

    def execute_batch(
        self,
        functions: List[Callable[[ExecutionContext], Any]],
        epoch_snapshot: Optional[EpochSnapshot] = None,
    ) -> List[Any]:

        results: List[Any] = []

        for fn in functions:
            results.append(self.execute(fn, epoch_snapshot))

        return results

    # =====================================================
    # ✅ AUDIT
    # =====================================================

    def get_audit_records(self) -> List[Dict[str, Any]]:
        return self._ledger.get_records()

    def commit_proofs(self, proofs: List[Dict[str, Any]]) -> Dict[str, Any]:
        block = self._ledger.commit_block(proofs)
        return block.to_dict()

    def get_audit_blocks(self) -> List[Dict[str, Any]]:
        return self._ledger.get_blocks()

    def verify_audit_chain(self) -> bool:
        return self._ledger.verify_chain()

    def clear_audit(self) -> None:
        self._ledger.clear()

    # =====================================================
    # ✅ INTERNAL VALIDATION
    # =====================================================

    def _validate_epoch_transition(self, epoch_snapshot: EpochSnapshot) -> None:

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid epoch transition")

        if self._last_epoch is None:
            return

        current = self._last_epoch.semantic_epoch.number
        incoming = epoch_snapshot.semantic_epoch.number

        if incoming < current:
            raise RuntimeError(
                f"Invalid epoch transition: {incoming} < {current}"
            )

    # =====================================================
    # ✅ STATE
    # =====================================================

    def is_initialized(self) -> bool:
        return self._initialized

    def get_current_epoch(self) -> Optional[int]:
        if self._last_epoch:
            return self._last_epoch.semantic_epoch.number
        return None

    def reset(self) -> None:

        self._admission.reset()
        self._ledger.clear()

        self._initialized = False
        self._last_epoch = None
