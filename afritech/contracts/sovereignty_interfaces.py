from __future__ import annotations

from typing import Protocol, Optional, Callable, Any, Dict
from dataclasses import dataclass
from abc import abstractmethod

from afritech.epoch.epoch_snapshot import EpochSnapshot


# ============================================================
# ✅ CONSTITUTIONAL RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class SovereigntyResult:
    """
    Result of a sovereignty validation.

    Guarantees:
    - Immutable
    - Deterministic
    - Replay-safe

    Attributes:
    - valid: whether the system is constitutionally valid
    - reason: optional explanation for failure
    - code: machine-readable reason identifier (required for audits)
    - metadata: structured context for debugging/replay
    """

    valid: bool
    reason: Optional[str] = None
    code: str = "UNKNOWN"
    metadata: Dict[str, Any] | None = None


# ============================================================
# ✅ GUARD INTERFACE CONTRACT
# ============================================================

class GuardInterface(Protocol):
    """
    Formal contract for all guard implementations.

    Guarantees:
    - Deterministic validation
    - No side effects
    - No runtime dependency leakage
    - Replay reproducibility

    MUST NOT:
    - import runtime modules
    - perform uncontrolled I/O
    - mutate global state
    """

    @abstractmethod
    def verify_sovereignty(
        self,
        epoch_snapshot: Optional[EpochSnapshot],
    ) -> SovereigntyResult:
        """
        Perform constitutional validation.

        Returns:
            SovereigntyResult
        """
        ...


# ============================================================
# ✅ EXECUTION ENTRY CONTRACT
# ============================================================

class SovereignExecutor(Protocol):
    """
    Contract for execution entrypoints enforcing sovereignty.

    Guarantees:
    - Guard validation MUST be executed first
    - Admission MUST be enforced
    - Kernel execution ONLY after admission
    - Audit MUST be recorded

    No bypass allowed.
    """

    @abstractmethod
    def execute(
        self,
        fn: Callable[[Any], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Any:
        """
        Execute a function under sovereign guarantees.

        MUST:
        - validate sovereignty
        - enforce admission
        - execute via kernel
        - record audit
        """
        ...


# ============================================================
# ✅ ADMISSION CONTRACT
# ============================================================

class AdmissionInterface(Protocol):
    """
    Contract for admission controllers.

    Guarantees:
    - Fail-closed behavior (default deny)
    - Deterministic decisions
    - Safe state transitions
    """

    @abstractmethod
    def admit(
        self,
        epoch_snapshot: Optional[EpochSnapshot],
    ) -> bool:
        """
        Decide if execution is allowed.
        """
        ...

    @abstractmethod
    def is_admitted(self) -> bool:
        """
        Check admission state.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset controller state.
        """
        ...


# ============================================================
# ✅ AUDIT CONTRACT
# ============================================================

class AuditInterface(Protocol):
    """
    Contract for audit logging systems.

    Guarantees:
    - Immutable logging
    - Replay traceability
    - No mutation of execution results
    """

    @abstractmethod
    def record(
        self,
        function_name: str,
        result: Any,
        context: Any,
    ) -> None:
        """
        Record execution outcome.

        MUST NOT modify inputs.
        """
        ...


# ============================================================
# ✅ EXECUTION CONTEXT CONTRACT
# ============================================================

class ExecutionContextInterface(Protocol):
    """
    Contract for execution context objects.

    Guarantees:
    - Carries epoch snapshot
    - Deterministic state representation
    - Replay-safe
    """

    epoch_snapshot: EpochSnapshot

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize context for replay/audit.

        MUST be deterministic.
        """
        ...


# ============================================================
# ✅ KERNEL CONTRACT
# ============================================================

class KernelInterface(Protocol):
    """
    Contract for execution kernels.

    Guarantees:
    - Execute only admitted requests
    - Deterministic execution
    - No uncontrolled side effects
    """

    @abstractmethod
    def execute(
        self,
        fn: Callable[[Any], Any],
        context: ExecutionContextInterface,
    ) -> Any:
        """
        Execute function in controlled kernel environment.
        """
        ...


# ============================================================
# ✅ OPTIONAL: ERROR TYPES
# ============================================================

class SovereigntyViolation(Exception):
    """
    Raised when sovereignty validation fails.
    """

    def __init__(self, result: SovereigntyResult):
        self.result = result
        super().__init__(f"[{result.code}] {result.reason}")


class AdmissionDenied(Exception):
    """
    Raised when admission is denied.
    """
    pass


class KernelExecutionError(Exception):
    """
    Raised for execution failures inside kernel.
    """
    pass


# ============================================================
# ✅ CONTRACT GUARANTEES (CRITICAL)
# ============================================================

"""
GA ELITE CONTRACT GUARANTEES

1. Determinism
   - Same input → same output (no randomness)

2. Replay Safety
   - All decisions reproducible from EpochSnapshot

3. Closed-World
   - No undeclared dependencies
   - No runtime introspection leaks

4. Layer Isolation
   - contracts layer is PURE (no dependencies on runtime/guards)

5. No Circular Imports
   - runtime → contracts → guards ✅
   - NEVER guards → runtime ❌

6. Fail-Closed System
   - Any failure → deny execution

7. Auditability
   - All results can be traced, serialized, and verified
"""


# ============================================================
# ✅ EXPORT
# ============================================================

__all__ = [
    "SovereigntyResult",
    "GuardInterface",
    "SovereignExecutor",
    "AdmissionInterface",
    "AuditInterface",
    "ExecutionContextInterface",
    "KernelInterface",
    "SovereigntyViolation",
    "AdmissionDenied",
    "KernelExecutionError",
]

