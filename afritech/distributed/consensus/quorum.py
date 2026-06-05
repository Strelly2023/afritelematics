from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class QuorumPolicy:
    mode: str = "majority"
    minimum_nodes: int = 1

    def required_votes(self, total_nodes: int) -> int:
        if not isinstance(total_nodes, int) or total_nodes <= 0:
            raise ValueError("total_nodes must be positive")

        if total_nodes < self.minimum_nodes:
            raise ValueError("total_nodes below minimum")

        if self.mode == "unanimous":
            required = total_nodes
        elif self.mode == "supermajority":
            required = ceil((total_nodes * 2) / 3)
        elif self.mode == "majority":
            required = (total_nodes // 2) + 1
        else:
            raise ValueError(f"unknown quorum mode: {self.mode}")

        return max(required, self.minimum_nodes)

    def has_quorum(self, votes: int, total_nodes: int) -> bool:
        if not isinstance(votes, int) or votes < 0:
            return False
        return votes >= self.required_votes(total_nodes)
