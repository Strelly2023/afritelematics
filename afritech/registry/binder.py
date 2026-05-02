from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from types import MappingProxyType

from afritech.state.state import State
from afritech.state.types import StateHash
from afritech.registry.merkle import build_merkle_tree


# ---------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Registry:
    """
    Immutable registry of constitutionally verified States.

    Invariants:
    - entries are immutable
    - keys are canonical StateHash values
    - root is deterministic over sorted keys
    """

    entries: Mapping[StateHash, State]
    root: str


# ---------------------------------------------------------------------
# Genesis root
# ---------------------------------------------------------------------

GENESIS_ROOT = "AFRITECH_REGISTRY_GENESIS"


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def _validate_state(state: State) -> None:
    """
    Constitutional admissibility check for registry binding.
    """

    if not hasattr(state, "attestation"):
        raise ValueError("STATE_MISSING_ATTESTATION")

    if not state.attestation.verified:
        raise ValueError("STATE_NOT_VERIFIED")

    if not state.attestation.state_hash:
        raise ValueError("STATE_HASH_MISSING")


# ---------------------------------------------------------------------
# Deterministic root computation
# ---------------------------------------------------------------------

def _compute_root(entries: Mapping[StateHash, State]) -> str:
    """
    Compute deterministic Merkle root.
    """

    if not entries:
        return GENESIS_ROOT

    ordered_hashes = sorted(entries.keys())

    tree = build_merkle_tree(ordered_hashes)

    if tree.root is None:
        return GENESIS_ROOT

    return tree.root.hash


# ---------------------------------------------------------------------
# Binding
# ---------------------------------------------------------------------

def bind_state(registry: Registry, state: State) -> Registry:
    """
    Bind a verified State into the registry.

    Guarantees:
    - verified states only
    - immutable registry evolution
    - deterministic Merkle recomputation
    - duplicate state hashes forbidden
    """

    _validate_state(state)

    state_hash = state.attestation.state_hash

    if state_hash in registry.entries:
        raise ValueError("STATE_ALREADY_BOUND")

    new_entries = dict(registry.entries)
    new_entries[state_hash] = state

    normalized_entries = MappingProxyType(
        dict(sorted(new_entries.items()))
    )

    return Registry(
        entries=normalized_entries,
        root=_compute_root(normalized_entries),
    )


# ---------------------------------------------------------------------
# Genesis registry
# ---------------------------------------------------------------------

def genesis_registry() -> Registry:
    """
    Create canonical empty sovereign registry.
    """

    return Registry(
        entries=MappingProxyType({}),
        root=GENESIS_ROOT,
    )