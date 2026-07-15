from __future__ import annotations

REPLAY_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"READY_FOR_EXECUTION", "CANCELLED"}),
    "READY_FOR_EXECUTION": frozenset({"EXECUTING", "CANCELLED"}),
    "EXECUTING": frozenset({"EXECUTED", "FAILED"}),
    "EXECUTED": frozenset({"VALIDATION_REQUIRED"}),
    "VALIDATION_REQUIRED": frozenset({"VALIDATED", "VALIDATION_FAILED"}),
    "VALIDATED": frozenset({"APPROVAL_REQUIRED"}),
    "APPROVAL_REQUIRED": frozenset({"APPROVED", "REJECTED", "EXPIRED"}),
    "APPROVED": frozenset({"PROMOTING", "EXPIRED"}),
    "PROMOTING": frozenset({"PROMOTED", "FAILED", "ROLLED_BACK"}),
    "PROMOTED": frozenset(),
    "FAILED": frozenset(),
    "VALIDATION_FAILED": frozenset(),
    "REJECTED": frozenset(),
    "CANCELLED": frozenset(),
    "EXPIRED": frozenset(),
    "ROLLED_BACK": frozenset(),
}


class InvalidReplayTransition(RuntimeError):
    pass


def ensure_replay_transition(current: str, target: str) -> None:
    allowed = REPLAY_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidReplayTransition(f"invalid_replay_transition:{current}->{target}")
