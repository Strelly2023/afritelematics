from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afritech.state.types import StateHash
from afritech.registry.binder import Registry
from afritech.registry.merkle import (
    build_merkle_tree,
    generate_proof,
    verify_proof,
    MerkleProof,
)


# ---------------------------------------------------------------------
# Proof snapshot (portable, read-only)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RegistryProof:
    """
    Portable proof object for external verification.

    - state_hash: the StateHash being proven
    - root: Merkle root of the registry snapshot
    - proof: Merkle inclusion proof
    """
    state_hash: StateHash
    root: str
    proof: MerkleProof


# ---------------------------------------------------------------------
# Proof export
# ---------------------------------------------------------------------

def export_proof(registry: Registry, state_hash: StateHash) -> RegistryProof:
    """
    Export an inclusion proof for a StateHash from a registry snapshot.

    Guarantees:
    - does not mutate registry
    - deterministic proof generation
    - no State inspection
    """

    if state_hash not in registry.entries:
        raise ValueError("STATE_NOT_REGISTERED")

    # Build Merkle view from registry entries (derived, discardable)
    tree = build_merkle_tree(list(registry.entries.keys()))

    proof = generate_proof(tree, state_hash)

    return RegistryProof(
        state_hash=state_hash,
        root=registry.root,
        proof=proof,
    )


# ---------------------------------------------------------------------
# Proof verification (standalone)
# ---------------------------------------------------------------------

def verify_registry_proof(snapshot: RegistryProof) -> bool:
    """
    Verify a RegistryProof without access to the registry.

    This function is fully standalone and deterministic.
    """

    return verify_proof(
        target=snapshot.state_hash,
        proof=snapshot.proof,
        root_hash=snapshot.root,
    )