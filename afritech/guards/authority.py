from __future__ import annotations

from dataclasses import dataclass

from afritech.state.state import State
from afritech.guards.engine import GuardResult, Guard


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
# Context-aware guard adapter
# ---------------------------------------------------------------------

def with_authority(
    guard_fn,
    context: GuardContext,
) -> Guard:
    """
    Adapt a (state, transition, context) guard into a standard Guard.
    """

    def guard(state: State, transition) -> GuardResult:
        return guard_fn(state, transition, context)

    return guard


# ---------------------------------------------------------------------
# Authority-aware guard implementations
# ---------------------------------------------------------------------

def require_role(required_role: str):
    def guard(state: State, transition, context: GuardContext) -> GuardResult:
        if required_role not in context.authority.roles:
            return GuardResult(False, f"ROLE_REQUIRED:{required_role}")
        return GuardResult(True)

    return guard


def forbid_attestation_claim(state: State, transition, context: GuardContext) -> GuardResult:
    candidate = transition(state)

    if candidate.attestation.verified:
        return GuardResult(False, "ATTESTATION_CLAIM_FORBIDDEN")

    return GuardResult(True)


def require_epoch_admin(state: State, transition, context: GuardContext) -> GuardResult:
    candidate = transition(state)

    if candidate.epoch != state.epoch:
        if "epoch_admin" not in context.authority.roles:
            return GuardResult(False, "EPOCH_ADMIN_REQUIRED")

    return GuardResult(True)
