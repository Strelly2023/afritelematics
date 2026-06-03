"""
afritech.contracts.guards_interface

Canonical interface contract for guard evaluation within AfriTech.

This module defines:
- Guard request/response structures
- Validation interfaces
- Deterministic guard execution boundaries

This is a PURE CONTRACT layer:
- No runtime imports
- No guard implementation logic
- No side effects

Purpose:
Break circular dependencies between:
- runtime
- admission
- guards

All guard implementations MUST comply with this interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol, Optional


# ============================================================
# CORE DATA STRUCTURES
# ============================================================

@dataclass(frozen=True)
class GuardContext:
    """
    Immutable context passed from runtime/admission into guards.

    Must be:
    - deterministic
    - serialization-safe
    - replay-safe
    """

    request_id: str
    timestamp: int
    actor_id: Optional[str]
    surface: str
    action: str
    payload_hash: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class GuardDecision:
    """
    Result of guard evaluation.

    Must be:
    - deterministic
    - explicit (no implicit defaults)
    """

    allowed: bool
    reason: str
    code: str  # machine-readable reason
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class GuardResult:
    """
    Full guard evaluation result.
    """

    decision: GuardDecision
    execution_time_ms: int
    guard_name: str


# ============================================================
# GUARD INTERFACE
# ============================================================

class Guard(Protocol):
    """
    Canonical guard interface.

    All guards must implement this protocol.

    Rules:
    - Must be pure (no side effects)
    - Must be deterministic
    - Must not import runtime modules
    """

    def evaluate(self, context: GuardContext) -> GuardResult:
        """
        Evaluate whether an operation is allowed.

        Args:
            context: GuardContext

        Returns:
            GuardResult

        Must NOT:
        - mutate input
        - depend on external state
        - perform I/O (unless abstracted and deterministic)
        """
        ...


# ============================================================
# VALIDATION INTERFACES
# ============================================================

class GuardValidator(Protocol):
    """
    Interface for validating guard results against rules.
    """

    def validate(self, result: GuardResult) -> bool:
        """
        Validate a guard result.

        Must be deterministic and side-effect free.
        """
        ...


# ============================================================
# EXCEPTIONS
# ============================================================

class GuardViolation(Exception):
    """
    Raised when a guard denies execution.
    """

    def __init__(self, decision: GuardDecision):
        self.decision = decision
        super().__init__(f"[{decision.code}] {decision.reason}")


class GuardExecutionError(Exception):
    """
    Raised when guard execution fails unexpectedly.
    """
    pass


# ============================================================
# UTILITY FUNCTIONS (PURE)
# ============================================================

def enforce_guard(result: GuardResult) -> None:
    """
    Enforce a guard result.

    Raises:
        GuardViolation if not allowed
    """
    if not result.decision.allowed:
        raise GuardViolation(result.decision)


def is_allowed(result: GuardResult) -> bool:
    """
    Convenience check.
    """
    return result.decision.allowed


# ============================================================
# CONTRACT GUARANTEES
# ============================================================

"""
CONSTITUTIONAL GUARANTEES:

1. Determinism
   - Same GuardContext must always produce same GuardResult

2. Closed-world safety
   - Guards must not discover or import undeclared runtime surfaces

3. Replay safety
   - Guard evaluation must be reproducible from context alone

4. Isolation
   - Guards must not depend on runtime internals

5. No circular dependencies
   - This contract is the ONLY shared dependency

ENFORCEMENT EXPECTATION:

runtime → contracts → guards
admission → contracts → guards

guards MUST NOT import:
- runtime
- admission
- kernel

This prevents topology violations like:
guards → runtime → admission → guards ❌
"""