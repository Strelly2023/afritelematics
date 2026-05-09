# afritech/guards/authority.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from afritech.state.state import State
from afritech.guards.guard_core import GuardResult
from afritech.guards.engine import fail, ViolationClass


# ---------------------------------------------------------------------
# Authority model (pure declaration)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Authority:
    actor_id: str
    roles: tuple[str, ...]


# ---------------------------------------------------------------------
# Guard context wrapper
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GuardContext:
    authority: Authority


# ---------------------------------------------------------------------
# Adapter: functional guard → strict enforcement
# ---------------------------------------------------------------------

def enforce_guard_result(result: GuardResult):
    """
    Convert GuardResult into constitutional enforcement.
    """

    if not result.ok:
        fail(
            result.reason or "authority_violation",
            ViolationClass.A_FATAL,
        )


# ---------------------------------------------------------------------
# Context-aware guard adapter
# ---------------------------------------------------------------------

def with_authority(
    guard_fn: Callable,
    context: GuardContext,
):
    """
    Wrap a functional guard into an enforcing guard.

    Usage:
        guarded = with_authority(require_role("admin"), ctx)
        guarded(state, transition)  # will fail() if violated
    """

    def guard(state: State, transition):

        result = guard_fn(state, transition, context)

        if not isinstance(result, GuardResult):
            fail(
                "invalid_guard_result_type",
                ViolationClass.B_STRUCTURAL,
            )

        enforce_guard_result(result)

        return True

    return guard


# ---------------------------------------------------------------------
# Authority-aware guard implementations
# ---------------------------------------------------------------------

def require_role(required_role: str):
    """
    Ensure actor has required role
    """

    def guard(state: State, transition, context: GuardContext) -> GuardResult:
        if required_role not in context.authority.roles:
            return GuardResult(False, f"ROLE_REQUIRED:{required_role}")
        return GuardResult(True)

    return guard


# ---------------------------------------------------------------------

def forbid_attestation_claim(
    state: State,
    transition,
    context: GuardContext,
) -> GuardResult:

    candidate = transition(state)

    if candidate.attestation.verified:
        return GuardResult(False, "ATTESTATION_CLAIM_FORBIDDEN")

    return GuardResult(True)


# ---------------------------------------------------------------------

def require_epoch_admin(
    state: State,
    transition,
    context: GuardContext,
) -> GuardResult:

    candidate = transition(state)

    if candidate.epoch != state.epoch:
        if "epoch_admin" not in context.authority.roles:
            return GuardResult(False, "EPOCH_ADMIN_REQUIRED")

    return GuardResult(True)