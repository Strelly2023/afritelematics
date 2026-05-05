from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from afritech.state.state import State
from afritech.state.types import JSONValue


# ---------------------------------------------------------------------
# Deep freeze (recursive, deterministic)
# ---------------------------------------------------------------------

def _freeze(value: JSONValue) -> JSONValue:
    """
    Recursively freeze JSONValue:

    - Mapping → MappingProxyType (immutable)
    - tuple → tuple (recursively frozen)
    - primitives → unchanged
    """

    if isinstance(value, Mapping):
        return MappingProxyType({
            k: _freeze(value[k])
            for k in value
        })

    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)

    return value


# ---------------------------------------------------------------------
# Freeze State payloads
# ---------------------------------------------------------------------

def freeze_state(state: State) -> State:
    """
    Return a fully frozen copy of State.

    Ensures:
    - no mutable payloads remain
    - safe for sharing across boundaries
    """

    return State(
        kernel_hash=state.kernel_hash,

        epoch=state.epoch,

        registry=type(state.registry)(
            payload=_freeze(state.registry.payload)
        ),

        vm=type(state.vm)(
            payload=_freeze(state.vm.payload)
        ),

        governance=type(state.governance)(
            payload=_freeze(state.governance.payload)
        ),

        provenance=state.provenance,
        attestation=state.attestation,
    )


# ---------------------------------------------------------------------
# Clone (safe duplication)
# ---------------------------------------------------------------------

def clone_state(state: State) -> State:
    """
    Create a deep, frozen clone of State.

    Equivalent to freeze_state but explicit for semantic clarity.
    """
    return freeze_state(state)