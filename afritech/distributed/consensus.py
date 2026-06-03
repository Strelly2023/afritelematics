from __future__ import annotations

from typing import List, Callable, Any, Dict
from collections import Counter
import json
import hashlib

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.runtime.kernel.execute import ExecutionContext
from afritech.distributed.node import SovereignNode


class ConsensusEngine:
    """
    Sovereign Consensus Engine.

    Responsibilities:
    - Execute across multiple nodes
    - Validate responses
    - Enforce deterministic consensus
    - Reject inconsistent results
    """

    def __init__(self, nodes: List[SovereignNode]) -> None:
        if not nodes:
            raise ValueError("ConsensusEngine requires at least one node")

        self.nodes: List[SovereignNode] = nodes

    # -----------------------------------------------------
    # Public execution
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Dict[str, Any]:
        """
        Execute function across nodes and derive consensus.

        Returns:
        {
            "result": Any,
            "votes": int,
            "total_nodes": int,
            "consensus_hash": str,
            "responses": list
        }
        """

        responses: List[Dict[str, Any]] = []

        # ✅ Execute on all nodes
        for node in self.nodes:
            try:
                response = node.execute(fn, epoch_snapshot)
            except Exception as e:
                response = {
                    "node": node.get_node_id(),
                    "status": "rejected",
                    "error": str(e),
                }

            responses.append(response)

        # ✅ Filter valid responses
        accepted = [
            r for r in responses
            if r.get("status") == "accepted" and "result" in r
        ]

        if not accepted:
            raise RuntimeError("Execution rejected by all nodes")

        # ✅ Deterministic hashing of results
        hashed_results: List[str] = [
            self._hash_result(r["result"])
            for r in accepted
        ]

        counts = Counter(hashed_results)
        consensus_hash, votes = counts.most_common(1)[0]

        # ✅ Require strict majority
        if votes <= len(self.nodes) // 2:
            raise RuntimeError("Consensus not reached")

        # ✅ Retrieve actual result (first matching)
        consensus_result = next(
            r["result"]
            for r in accepted
            if self._hash_result(r["result"]) == consensus_hash
        )

        return {
            "result": consensus_result,
            "votes": votes,
            "total_nodes": len(self.nodes),
            "consensus_hash": consensus_hash,
            "responses": responses,
        }

    # -----------------------------------------------------
    # Deterministic hash utility
    # -----------------------------------------------------

    def _hash_result(self, result: Any) -> str:
        """
        Deterministic result hashing for consensus comparison.
        """

        try:
            serialized = json.dumps(
                result,
                sort_keys=True,   # ✅ deterministic ordering
                default=str       # ✅ fallback safe
            )
        except Exception:
            serialized = str(result)

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()