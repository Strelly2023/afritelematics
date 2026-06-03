from __future__ import annotations

import hashlib
from typing import List, Dict


class MerkleTree:
    """
    Builds a Merkle Tree from audit log hashes.

    Leaves = entry_hash values
    """

    def __init__(self, leaf_hashes: List[str]):
        if not leaf_hashes:
            raise ValueError("EMPTY_MERKLE_INPUT")

        self.leaves: List[str] = leaf_hashes
        self.levels: List[List[str]] = []
        self._build_tree()

    # =====================================================
    # ✅ CORE TREE BUILD
    # =====================================================

    def _build_tree(self) -> None:
        """
        Builds tree levels from leaves → root.
        """

        current_level = self.leaves.copy()
        self.levels.append(current_level)

        while len(current_level) > 1:
            current_level = self._build_next_level(current_level)
            self.levels.append(current_level)

    def _build_next_level(self, level: List[str]) -> List[str]:
        """
        Pairs adjacent nodes and hashes them.
        """

        next_level: List[str] = []

        for i in range(0, len(level), 2):
            left = level[i]

            # ✅ duplicate last node if odd count
            right = level[i + 1] if i + 1 < len(level) else left

            combined = self._hash_pair(left, right)
            next_level.append(combined)

        return next_level

    # =====================================================
    # ✅ HASHING
    # =====================================================

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """
        Hashes two nodes into one.
        """

        base = f"{left}:{right}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    # =====================================================
    # ✅ ROOT ACCESS
    # =====================================================

    def get_root(self) -> str:
        """
        Returns Merkle root hash.
        """

        return self.levels[-1][0]

    # =====================================================
    # ✅ PROOF GENERATION
    # =====================================================

    def get_proof(self, index: int) -> List[Dict[str, str]]:
        """
        Generates inclusion proof for a leaf.

        Proof format:
        [
            {"hash": "...", "position": "left" or "right"},
            ...
        ]
        """

        if index < 0 or index >= len(self.leaves):
            raise ValueError("INVALID_LEAF_INDEX")

        proof: List[Dict[str, str]] = []
        current_index = index

        for level in self.levels[:-1]:
            level_length = len(level)

            is_right_node = current_index % 2
            sibling_index = (
                current_index - 1 if is_right_node
                else current_index + 1
            )

            if sibling_index < level_length:
                sibling_hash = level[sibling_index]
            else:
                # ✅ duplicate self if no sibling (odd node)
                sibling_hash = level[current_index]

            proof.append({
                "position": "left" if is_right_node else "right",
                "hash": sibling_hash,
            })

            current_index = current_index // 2

        return proof

    # =====================================================
    # ✅ PROOF VERIFICATION
    # =====================================================

    @staticmethod
    def verify_proof(
        leaf_hash: str,
        proof: List[Dict[str, str]],
        root: str
    ) -> bool:
        """
        Verifies inclusion of leaf in Merkle tree.
        """

        computed_hash = leaf_hash

        for step in proof:
            if step["position"] == "left":
                combined = f"{step['hash']}:{computed_hash}"
            else:
                combined = f"{computed_hash}:{step['hash']}"

            computed_hash = hashlib.sha256(
                combined.encode("utf-8")
            ).hexdigest()

        return computed_hash == root