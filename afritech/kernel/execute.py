# afritech/runtime/kernel/execute.py

"""
AfriTech Constitutional Execution Kernel
========================================

This module defines the SINGLE lawful execution entrypoint
for the AfriTech runtime.

All execution MUST pass through this kernel.

Responsibilities:
- Enforce sovereignty (epoch, registry, kernel integrity)
- Enforce deterministic execution (AST-level)
- Enforce runtime context integrity
- Collapse execution authority into a single gate
- Delegate execution to the ExecutionEngine
- Fail closed on any violation
"""

from __future__ import annotations

from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.engine.executor import (
    ExecutionEngine,
    ExecutionResult,
)
from afritech.guards.engine import verify_sovereignty
from afritech.runtime.guards.determinism_guard import (
    enforce_determinism,
    DeterminismViolation,
)


# ---------------------------------------------------------------------
# Constitutional halt
# ---------------------------------------------------------------------

def constitutional_halt(message: str) -> None:
    raise SystemExit(
        f"\n❌ CONSTITUTIONAL EXECUTION HALT\n{message}\n"
    )


# ---------------------------------------------------------------------
# Canonical execution kernel
# ---------------------------------------------------------------------

def EXECUTE(
    *,
    engine: ExecutionEngine,
    context: RuntimeContext,
) -> ExecutionResult:
    """
    Canonical constitutional execution gate.

    This is the ONLY function permitted to invoke
    ExecutionEngine.execute().

    Any execution path that bypasses this function
    is constitutionally invalid.
    """

    # -------------------------------------------------------------
    # 1. Runtime context integrity
    # -------------------------------------------------------------

    if not isinstance(context, RuntimeContext):
        constitutional_halt("Invalid runtime context type")

    if not context.verify():
        constitutional_halt(
            "Runtime context integrity verification failed"
        )

    # -------------------------------------------------------------
    # 2. Sovereignty enforcement (HARD LAW)
    # -------------------------------------------------------------
    # Enforces:
    # - sealed registry
    # - epoch authority
    # - kernel immutability
    # - constitutional surface hashes
    # -------------------------------------------------------------

    try:
        verify_sovereignty(context)
    except Exception as e:
        constitutional_halt(
            f"Sovereignty verification failed: {e}"
        )

    # -------------------------------------------------------------
    # 3. Determinism enforcement (AST-LEVEL, HARD LAW)
    # -------------------------------------------------------------
    # This is the critical Kernel v1 closure:
    # - No time
    # - No randomness
    # - No environment
    # - No I/O
    # - No concurrency
    # -------------------------------------------------------------

    try:
        enforce_determinism(
            execution_fn=engine.execution_fn
        )
    except DeterminismViolation as e:
        constitutional_halt(
            f"Determinism violation detected:\n{e}"
        )

    # -------------------------------------------------------------
    # 4. Delegate to execution engine (MECHANISM)
    # -------------------------------------------------------------

    try:
        result = engine.execute(context)
    except Exception as e:
        constitutional_halt(
            f"Execution engine raised unhandled exception: {e}"
        )

    # -------------------------------------------------------------
    # 5. Post-execution integrity
    # -------------------------------------------------------------

    if not isinstance(result, ExecutionResult):
        constitutional_halt(
            "Execution did not return ExecutionResult"
        )

    if not result.verify():
        constitutional_halt(
            "ExecutionResult integrity verification failed"
        )

    # -------------------------------------------------------------
    # ✅ Execution constitutionally admitted
    # -------------------------------------------------------------

    return result