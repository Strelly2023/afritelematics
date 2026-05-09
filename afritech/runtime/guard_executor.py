# afritech/runtime/guard_executor.py

from __future__ import annotations

"""
AfriTech Runtime Guard Executor
===============================

Lawful sovereign transition dispatcher.

Responsibilities:
- deterministic guard evaluation
- guarded transition execution
- explicit constitutional rejection
- sovereign runtime activation
- TRACE‑backed causal execution

This is a CRITICAL constitutional surface.
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from afritech.state.state import State
from afritech.state.types import TransitionId
from afritech.transition.engine import (
    apply_transition,
    Transition,
)
from afritech.guards.engine import ConstitutionalViolation

from afritech.trace.trace_engine import TraceEngine
from afritech.trace.trace_context import TraceContext


# ---------------------------------------------------------------------
# Runtime constitutional halt
# ---------------------------------------------------------------------

def runtime_halt(message: str) -> None:
    raise ConstitutionalViolation(
        f"\n❌ RUNTIME CONSTITUTIONAL VIOLATION\n{message}\n"
    )


# ---------------------------------------------------------------------
# Guard result model
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GuardResult:
    ok: bool
    reason: str | None = None


# Pure predicate over (state, transition)
Guard = Callable[[State, Transition], GuardResult]


# ---------------------------------------------------------------------
# Guarded transition result
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TransitionResult:
    accepted: bool
    state: State | None
    violations: tuple[str, ...]
    trace_hash: Optional[str] = None


# ---------------------------------------------------------------------
# Guard evaluation (DETERMINISTIC)
# ---------------------------------------------------------------------

def evaluate_guards(
    state: State,
    transition: Transition,
    guards: Iterable[Guard],
    *,
    trace: Optional[TraceEngine] = None,
) -> tuple[bool, tuple[str, ...]]:
    """
    Evaluate guards deterministically.

    TRACE:
    - records each guard decision
    """

    violations: list[str] = []

    for guard in guards:
        result = guard(state, transition)

        if trace:
            trace.record(
                "guard_evaluation",
                {
                    "guard": guard.__name__,
                    "ok": result.ok,
                    "reason": result.reason,
                },
            )
            trace.complete(
                "guard_evaluation",
                {"status": "ok" if result.ok else "violation"},
            )

        if not result.ok:
            violations.append(
                result.reason or "UNKNOWN_VIOLATION"
            )

    return (len(violations) == 0, tuple(violations))


# ---------------------------------------------------------------------
# Guarded transition execution
# ---------------------------------------------------------------------

def apply_guarded_transition(
    state: State,
    transition: Transition,
    transition_id: TransitionId,
    guards: Iterable[Guard],
    *,
    trace: Optional[TraceEngine] = None,
) -> TransitionResult:
    """
    Apply transition only if all guards pass.

    Guarantees:
    - deterministic guard ordering
    - no partial mutation
    - explicit rejection semantics
    - TRACE‑provable causality
    """

    if trace:
        trace.record(
            "guarded_transition_start",
            {
                "transition_id": str(transition_id),
                "state": state.id,
            },
        )

    ok, violations = evaluate_guards(
        state,
        transition,
        guards,
        trace=trace,
    )

    if not ok:
        if trace:
            trace.complete(
                "guarded_transition_start",
                {
                    "accepted": False,
                    "violations": violations,
                },
            )
            trace_hash = trace.finalize()
        else:
            trace_hash = None

        return TransitionResult(
            accepted=False,
            state=None,
            violations=violations,
            trace_hash=trace_hash,
        )

    try:
        new_state = apply_transition(
            state,
            transition,
            transition_id,
        )
    except Exception as exc:
        runtime_halt(
            f"Transition execution failed:\n{exc}"
        )

    if trace:
        trace.complete(
            "guarded_transition_start",
            {
                "accepted": True,
                "new_state": new_state.id,
            },
        )
        trace_hash = trace.finalize()
    else:
        trace_hash = None

    return TransitionResult(
        accepted=True,
        state=new_state,
        violations=(),
        trace_hash=trace_hash,
    )


# ---------------------------------------------------------------------
# Sovereign runtime activation
# ---------------------------------------------------------------------

def run() -> None:
    """
    Runtime authority activation.

    This establishes lawful execution capability
    after constitutional boot verification.
    """

    print("⚙️ Guard executor activated")
    print("✅ Runtime authority established")