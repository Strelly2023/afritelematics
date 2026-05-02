from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Tuple

from afritech.state.types import StateHash


# ---------------------------------------------------------------------
# Hash helper (bytes → hex string)
# ---------------------------------------------------------------------

def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    """
    Deterministic parent hash from two child hashes.
    """
    return _hash_bytes((left + right).encode("utf-8"))


# ---------------------------------------------------------------------
# Merkle Tree Node (immutable structure)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MerkleNode:
    hash: str
    left: MerkleNode | None = None
    right: MerkleNode | None = None


# ---------------------------------------------------------------------
# Merkle Tree (immutable, deterministic)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MerkleTree:
    root: MerkleNode
    leaves: Tuple[MerkleNode, ...]


# ---------------------------------------------------------------------
# Build tree from StateHash list
# ---------------------------------------------------------------------

def build_merkle_tree(state_hashes: List[StateHash]) -> MerkleTree:
    """
    Build a deterministic Merkle tree from StateHash values.

    Rules:
    - Input order is canonicalized (sorted)
    - Tree is fully deterministic
    - If odd number of leaves, last is duplicated
    """

    if not state_hashes:
        raise ValueError("EMPTY_REGISTRY")

    # -----------------------------------------------------------------
    # 1. Canonical ordering (critical for determinism)
    # -----------------------------------------------------------------
    ordered = sorted(str(h) for h in state_hashes)

    # -----------------------------------------------------------------
    # 2. Create leaf nodes
    # -----------------------------------------------------------------
    leaves = tuple(MerkleNode(hash=h) for h in ordered)

    current_level = list(leaves)

    # -----------------------------------------------------------------
    # 3. Build upward
    # -----------------------------------------------------------------
    while len(current_level) > 1:
        next_level: List[MerkleNode] = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]

            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                # duplicate last node if odd
                right = left

            parent_hash = _hash_pair(left.hash, right.hash)

            next_level.append(
                MerkleNode(
                    hash=parent_hash,
                    left=left,
                    right=right,
                )
            )

        current_level = next_level

    return MerkleTree(
        root=current_level[0],
        leaves=leaves,
    )


# ---------------------------------------------------------------------
# Inclusion proof
# ---------------------------------------------------------------------

# Each proof step = (sibling_hash, is_left_sibling)
MerkleProof = Tuple[Tuple[str, bool], ...]


def generate_proof(tree: MerkleTree, target: StateHash) -> MerkleProof:
    """
    Generate inclusion proof for a given StateHash.
    """

    target_hash = str(target)

    # find leaf index
    try:
        index = next(i for i, leaf in enumerate(tree.leaves) if leaf.hash == target_hash)
    except StopIteration:
        raise ValueError("STATE_NOT_IN_TREE")

    proof: List[Tuple[str, bool]] = []
    current_level = list(tree.leaves)

    while len(current_level) > 1:
        next_level: List[MerkleNode] = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]

            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left

            # track sibling
            if i == index or i + 1 == index:
                if index == i:
                    # current node is left
                    proof.append((right.hash, False))  # sibling is right
                else:
                    proof.append((left.hash, True))   # sibling is left

                index = len(next_level)

            parent_hash = _hash_pair(left.hash, right.hash)

            next_level.append(
                MerkleNode(
                    hash=parent_hash,
                    left=left,
                    right=right,
                )
            )

        current_level = next_level

    return tuple(proof)


# ---------------------------------------------------------------------
# Proof verification (no registry needed)
# ---------------------------------------------------------------------

def verify_proof(
    target: StateHash,
    proof: MerkleProof,
    root_hash: str,
) -> bool:
    """
    Verify inclusion proof without access to the full tree.
    """

    current_hash = str(target)

    for sibling_hash, is_left in proof:
        if is_left:
            current_hash = _hash_pair(sibling_hash, current_hash)
        else:
            current_hash = _hash_pair(current_hash, sibling_hash)

    return current_hash == root_hash