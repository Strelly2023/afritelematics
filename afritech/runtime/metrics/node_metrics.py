from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Dict


@dataclass(frozen=True)
class NodeMetrics:
    node_id: str
    active_peers: int
    proofs_emitted: int
    trust_score: float
    timestamp: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "node_id": self.node_id,
            "active_peers": self.active_peers,
            "proofs_emitted": self.proofs_emitted,
            "trust_score": self.trust_score,
            "timestamp": self.timestamp,
        }


def build_node_metrics(
    node_id: str,
    active_peers: int = 0,
    proofs_emitted: int = 0,
    trust_score: float = 100.0,
) -> NodeMetrics:
    return NodeMetrics(
        node_id=node_id,
        active_peers=active_peers,
        proofs_emitted=proofs_emitted,
        trust_score=trust_score,
        timestamp=time.time(),
    )
