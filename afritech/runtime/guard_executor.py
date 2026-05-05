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
"""

from dataclasses import dataclass
from typing import Callable, Iterable

from afritech.state.state import State
from afritech.state.types import TransitionId
from afritech.transition.engine import (
    apply_transition,
    Transition,
)
from afritech.guards.engine import ConstitutionalViolation

#afritech/runtime/guard_executor.py
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


# ---------------------------------------------------------------------
# Guard evaluation
# ---------------------------------------------------------------------

def evaluate_guards(
    state: State,
    transition: Transition,
    guards: Iterable[Guard],
) -> tuple[bool, tuple[str, ...]]:
    """
    Evaluate guards deterministically.

    Returns:
        (accepted, violations)
    """

    violations: list[str] = []

    for guard in guards:
        result = guard(state, transition)

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
) -> TransitionResult:
    """
    Apply transition only if all guards pass.

    Guarantees:
    - deterministic guard ordering
    - no partial mutation
    - explicit rejection semantics
    """

    ok, violations = evaluate_guards(
        state,
        transition,
        guards,
    )

    if not ok:
        return TransitionResult(
            accepted=False,
            state=None,
            violations=violations,
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

    return TransitionResult(
        accepted=True,
        state=new_state,
        violations=(),
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