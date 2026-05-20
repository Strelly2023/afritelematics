"""Explicitly frozen non-operational surface for ecosystems.afriride.domain.invariants.ride_rules."""

from __future__ import annotations


IMPLEMENTATION_STATE = "FROZEN"
RUNTIME_ADMISSIBLE = False
REPLAY_PARTICIPATING = False
PROOF_ADMISSIBLE = False
MUTATION_AUTHORITY = False
FREEZE_REASON = (
    "Surface existed as an empty Python module. It is resolved as "
    "FROZEN until a constitutional implementation admits runtime, "
    "replay, proof, and witness behavior."
)


class FrozenSurfaceError(RuntimeError):
    """Raised when a frozen surface is invoked as executable."""


def assert_admissible() -> None:
    """Fail closed for any accidental runtime activation."""

    raise FrozenSurfaceError(FREEZE_REASON)


def is_runtime_admissible() -> bool:
    """Return the explicit runtime admissibility state."""

    return RUNTIME_ADMISSIBLE
