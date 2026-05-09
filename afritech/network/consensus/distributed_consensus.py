import hashlib
import json
from datetime import datetime


class ConsensusError(Exception):
    """Raised when node consensus fails"""
    pass


# -----------------------------------------------------------------
# CONSENSUS RESULT
# -----------------------------------------------------------------

class ConsensusResult:

    def __init__(
        self,
        agreed: bool,
        votes: int,
        required: int,
        total: int,
        winning_hash: str
    ):
        self.agreed = agreed
        self.votes = votes
        self.required = required
        self.total = total
        self.winning_hash = winning_hash
        self.generated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "agreed": self.agreed,
            "votes": self.votes,
            "required": self.required,
            "total_nodes": self.total,
            "winning_hash": self.winning_hash,
            "generated_at": self.generated_at
        }


# -----------------------------------------------------------------
# NODE CLIENT
# -----------------------------------------------------------------

class NodeClient:

    def __init__(self, node_id: str, endpoint_fn):
        self.node_id = node_id
        self.endpoint_fn = endpoint_fn

    def execute(self, request):
        return self.endpoint_fn(request)


# -----------------------------------------------------------------
# CONSENSUS ENGINE
# -----------------------------------------------------------------

class DistributedConsensus:

    def __init__(self, nodes, threshold_ratio=0.66):

        if not nodes:
            raise ValueError("Consensus requires at least one node")

        self.nodes = nodes
        self.threshold_ratio = threshold_ratio

    # -----------------------------------------------------------------
    # CANONICAL JSON
    # -----------------------------------------------------------------

    def canonical_json(self, data):
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    # -----------------------------------------------------------------
    # HASH RESULT (TRUE SYSTEM ALIGNMENT)
    # -----------------------------------------------------------------

    def hash_result(self, result: dict) -> str:
        """
        Uses ExecutionResult.result_hash if available.
        Falls back to canonical hashing.
        """

        if "result_hash" in result:
            return result["result_hash"]

        # fallback (rare / defensive)
        return hashlib.sha256(
            self.canonical_json(result).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # MAIN CONSENSUS EXECUTION
    # -----------------------------------------------------------------

    def execute_with_consensus(self, request):

        results = []
        votes = {}
        errors = []

        # -------------------------------------------------------------
        # 1. COLLECT
        # -------------------------------------------------------------
        for node in self.nodes:

            try:
                result = node.execute(request)

                if not isinstance(result, dict):
                    raise ValueError("Invalid result format")

                result_hash = self.hash_result(result)

                results.append({
                    "node_id": node.node_id,
                    "result": result,
                    "hash": result_hash
                })

                votes[result_hash] = votes.get(result_hash, 0) + 1

            except Exception as e:
                errors.append({
                    "node_id": node.node_id,
                    "error": str(e)
                })

        # -------------------------------------------------------------
        # 2. CONSENSUS CALCULATION
        # -------------------------------------------------------------
        total_nodes = len(self.nodes)
        required_votes = int(total_nodes * self.threshold_ratio) + 1

        best_hash = None
        best_votes = 0

        for h, count in votes.items():
            if count > best_votes:
                best_votes = count
                best_hash = h

        agreed = best_votes >= required_votes

        consensus = ConsensusResult(
            agreed,
            best_votes,
            required_votes,
            total_nodes,
            best_hash
        )

        # -------------------------------------------------------------
        # 3. FAILURE
        # -------------------------------------------------------------
        if not agreed:
            raise ConsensusError({
                "message": "Consensus not reached",
                "votes_distribution": votes,
                "errors": errors,
                "required": required_votes,
                "total": total_nodes
            })

        # -------------------------------------------------------------
        # 4. SELECT WINNER
        # -------------------------------------------------------------
        winning = next(
            r["result"]
            for r in results
            if r["hash"] == best_hash
        )

        # -------------------------------------------------------------
        # 5. RETURN
        # -------------------------------------------------------------
        return {
            "consensus": consensus.to_dict(),
            "result": winning,
            "node_failures": errors
        }
