from __future__ import annotations

from .enums import CapabilityState
from .errors import InvalidTransitionError


ALLOWED_TRANSITIONS: dict[CapabilityState, set[CapabilityState]] = {
    CapabilityState.NOT_CONFIGURED: {CapabilityState.CONFIGURED, CapabilityState.BLOCKED},
    CapabilityState.CONFIGURED: {CapabilityState.EXECUTION_PENDING, CapabilityState.RUNNING, CapabilityState.BLOCKED},
    CapabilityState.EXECUTION_PENDING: {CapabilityState.RUNNING, CapabilityState.BLOCKED},
    CapabilityState.RUNNING: {CapabilityState.EXECUTED, CapabilityState.FAILED},
    CapabilityState.EXECUTED: {CapabilityState.VERIFICATION_PENDING, CapabilityState.FAILED},
    CapabilityState.VERIFICATION_PENDING: {CapabilityState.VERIFIED, CapabilityState.FAILED, CapabilityState.BLOCKED},
    CapabilityState.VERIFIED: {CapabilityState.CERTIFICATION_PENDING, CapabilityState.EXPIRED, CapabilityState.REVOKED},
    CapabilityState.CERTIFICATION_PENDING: {CapabilityState.CERTIFIED, CapabilityState.FAILED, CapabilityState.BLOCKED},
    CapabilityState.CERTIFIED: {CapabilityState.APPROVAL_PENDING, CapabilityState.EXPIRED, CapabilityState.REVOKED},
    CapabilityState.APPROVAL_PENDING: {CapabilityState.APPROVED, CapabilityState.REVOKED, CapabilityState.BLOCKED},
    CapabilityState.APPROVED: {CapabilityState.EXPIRED, CapabilityState.REVOKED},
    CapabilityState.FAILED: {CapabilityState.EXECUTION_PENDING, CapabilityState.BLOCKED},
    CapabilityState.BLOCKED: {CapabilityState.CONFIGURED, CapabilityState.REVOKED},
    CapabilityState.EXPIRED: {CapabilityState.CONFIGURED, CapabilityState.REVOKED},
    CapabilityState.REVOKED: set(),
}


FORBIDDEN_SHORTCUTS = {
    (CapabilityState.CONFIGURED, CapabilityState.VERIFIED),
    (CapabilityState.EXECUTED, CapabilityState.APPROVED),
    (CapabilityState.CONFIGURED, CapabilityState.APPROVED),
    (CapabilityState.VERIFIED, CapabilityState.APPROVED),
}


def assert_transition_allowed(previous: CapabilityState, target: CapabilityState, actor_type: str = "SYSTEM") -> None:
    if actor_type == "CLIENT_REQUEST" and target == CapabilityState.APPROVED:
        raise InvalidTransitionError("client_request_cannot_approve")
    if (previous, target) in FORBIDDEN_SHORTCUTS or target not in ALLOWED_TRANSITIONS.get(previous, set()):
        raise InvalidTransitionError(f"invalid_transition:{previous.value}->{target.value}")
