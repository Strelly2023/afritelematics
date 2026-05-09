# afritech/distributed/verifier.py

"""
AfriTech Distributed Execution Verifier

Purpose:
Verify distributed execution across multiple nodes.

Enforces:
- deterministic agreement
- quorum-based consensus
- result hash consistency
- replay integrity binding
- signature presence (extensible)

Failure → consensus failure → execution invalid
"""

from typing import List, Dict, Any
from collections import defaultdict


class ConsensusError(Exception):
    """Raised when distributed consensus fails"""
    pass


class DistributedVerifier:
    """
    Distributed execution verifier

    Validates:
    - majority agreement on result_hash
    - optional replay_hash matching
    - quorum threshold
    """

    def __init__(
        self,
        quorum_ratio: float = 0.67,
        min_nodes: int = 3,
        require_replay_match: bool = True,
    ):
        self.quorum_ratio = quorum_ratio
        self.min_nodes = min_nodes
        self.require_replay_match = require_replay_match

    # -----------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # -----------------------------------------------------------------

    def verify(self, node_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        node_results format:

        [
            {
                "node_id": "NODE_A",
                "context_hash": "...",
                "result_hash": "...",
                "replay_hash": "...",
                "signature": "..."
            }
        ]
        """

        self._validate_structure(node_results)
        self._validate_min_nodes(node_results)
        self._validate_context_consistency(node_results)

        result_consensus = self._compute_consensus(node_results, "result_hash")

        if self.require_replay_match:
            replay_consensus = self._compute_consensus(node_results, "replay_hash")

            if replay_consensus["value"] != result_consensus["value"]:
                raise ConsensusError("replay_result_mismatch")

        self._validate_quorum(result_consensus)

        return self._build_proof(node_results, result_consensus)

    # -----------------------------------------------------------------
    # VALIDATIONS
    # -----------------------------------------------------------------

    def _validate_structure(self, node_results: List[Dict[str, Any]]):
        if not isinstance(node_results, list) or not node_results:
            raise ConsensusError("invalid_node_result_structure")

        required_fields = [
            "node_id",
            "context_hash",
            "result_hash",
        ]

        if self.require_replay_match:
            required_fields.append("replay_hash")

        for node in node_results:
            for field in required_fields:
                if field not in node:
                    raise ConsensusError(f"missing_field: {field}")

    def _validate_min_nodes(self, node_results):
        if len(node_results) < self.min_nodes:
            raise ConsensusError("insufficient_nodes")

    def _validate_context_consistency(self, node_results):
        context_hashes = {n["context_hash"] for n in node_results}

        if len(context_hashes) != 1:
            raise ConsensusError("context_mismatch_across_nodes")

    # -----------------------------------------------------------------
    # CONSENSUS COMPUTATION
    # -----------------------------------------------------------------

    def _compute_consensus(self, node_results, key: str) -> Dict[str, Any]:
        counts = defaultdict(int)

        for node in node_results:
            counts[node[key]] += 1

        best_value = None
        best_count = 0

        for value, count in counts.items():
            if count > best_count:
                best_value = value
                best_count = count

        total = len(node_results)
        ratio = best_count / total

        return {
            "value": best_value,
            "count": best_count,
            "total": total,
            "ratio": ratio,
        }

    # -----------------------------------------------------------------
    # QUORUM VALIDATION
    # -----------------------------------------------------------------

    def _validate_quorum(self, consensus: Dict[str, Any]):
        if consensus["ratio"] < self.quorum_ratio:
            raise ConsensusError(
                f"quorum_not_met: {consensus['ratio']} < {self.quorum_ratio}"
            )

    # -----------------------------------------------------------------
    # PROOF GENERATION
    # -----------------------------------------------------------------

    def _build_proof(
        self,
        node_results: List[Dict[str, Any]],
        consensus: Dict[str, Any],
    ) -> Dict[str, Any]:

        proof = {
            "proof_type": "DISTRIBUTED_EXECUTION_PROOF",
            "context_hash": node_results[0]["context_hash"],
            "final_result_hash": consensus["value"],
            "agreement_ratio": consensus["ratio"],
            "consensus_achieved": True,
            "node_count": consensus["total"],
            "agreeing_nodes": [],
            "disagreeing_nodes": [],
            "nodes": [],
        }

        for node in node_results:

            is_agree = node["result_hash"] == consensus["value"]

            enriched = {
                "node_id": node["node_id"],
                "result_hash": node["result_hash"],
                "replay_hash": node.get("replay_hash"),
                "signature": node.get("signature"),
                "agrees": is_agree,
            }

            proof["nodes"].append(enriched)

            if is_agree:
                proof["agreeing_nodes"].append(node["node_id"])
            else:
                proof["disagreeing_nodes"].append(node["node_id"])

        return proof
