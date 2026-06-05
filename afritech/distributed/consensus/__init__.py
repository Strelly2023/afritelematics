from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any, Callable, Dict, List

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.runtime.kernel.execute import ExecutionContext


class ConsensusEngine:
    """
    Backward-compatible result consensus engine.
    """

    def __init__(self, nodes: List[Any]) -> None:
        if not nodes:
            raise ValueError("ConsensusEngine requires at least one node")
        self.nodes = nodes

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Dict[str, Any]:
        responses: List[Dict[str, Any]] = []

        for node in self.nodes:
            try:
                response = node.execute(fn, epoch_snapshot)
            except Exception as exc:
                response = {
                    "node": node.get_node_id(),
                    "status": "rejected",
                    "error": str(exc),
                }
            responses.append(response)

        accepted = [
            r for r in responses
            if r.get("status") == "accepted" and "result" in r
        ]
        if not accepted:
            raise RuntimeError("Execution rejected by all nodes")

        counts = Counter(self._hash_result(r["result"]) for r in accepted)
        consensus_hash, votes = counts.most_common(1)[0]
        if votes <= len(self.nodes) // 2:
            raise RuntimeError("Consensus not reached")

        result = next(
            r["result"] for r in accepted
            if self._hash_result(r["result"]) == consensus_hash
        )
        return {
            "result": result,
            "votes": votes,
            "total_nodes": len(self.nodes),
            "consensus_hash": consensus_hash,
            "responses": responses,
        }

    def _hash_result(self, result: Any) -> str:
        try:
            serialized = json.dumps(result, sort_keys=True, default=str)
        except Exception:
            serialized = str(result)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


from afritech.distributed.consensus.consensus_engine import ProofConsensusEngine

__all__ = ["ConsensusEngine", "ProofConsensusEngine"]
