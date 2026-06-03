"""AfriProgramming Phase 0 deterministic sandbox.

This file is the bounded execution surface for Phase 0.

It must remain:
- deterministic
- replay-safe
- side-effect free
- non-authoritative
"""

from __future__ import annotations


SURFACE_ID = "afritech.ecosystems.afriprogramming.execution.sandbox"


def run_user_function(x: int) -> int:
    """Deterministic user function for Phase 0."""

    if not isinstance(x, int):
        raise TypeError("Phase 0 sandbox input must be int")

    return x * 2


def surface_metadata() -> dict[str, object]:
    """Return deterministic metadata for this execution surface."""

    return {
        "surface_id": SURFACE_ID,
        "phase": 0,
        "deterministic": True,
        "replay_safe": True,
        "side_effect_free": True,
        "authority": "NONE",
    }