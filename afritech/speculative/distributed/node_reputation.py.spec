# afritech/distributed/node_reputation.py

"""
AfriTech Node Reputation & Quarantine System

Purpose:
Track node behavior across distributed execution and enforce:

- reputation scoring
- anomaly detection
- automatic quarantine
- trust-based participation

This system is deterministic and replay-safe.
"""

from typing import Dict, Any, List


class ReputationError(Exception):
    pass


class NodeStatus:
    ACTIVE = "ACTIVE"
    WATCHLIST = "WATCHLIST"
    QUARANTINED = "QUARANTINED"


class NodeReputationManager:

    def __init__(
        self,
        initial_score: float = 1.0,
        penalty_mismatch: float = 0.2,
        penalty_replay_failure: float = 0.3,
        penalty_invalid_signature: float = 0.3,
        reward_agreement: float = 0.05,
        quarantine_threshold: float = 0.4,
        watchlist_threshold: float = 0.7,
    ):
        self.nodes: Dict[str, Dict[str, Any]] = {}

        self.initial_score = initial_score

        self.penalty_mismatch = penalty_mismatch
        self.penalty_replay_failure = penalty_replay_failure
        self.penalty_invalid_signature = penalty_invalid_signature
        self.reward_agreement = reward_agreement

        self.quarantine_threshold = quarantine_threshold
        self.watchlist_threshold = watchlist_threshold

    # -----------------------------------------------------------------
    # NODE INIT
    # -----------------------------------------------------------------

    def _ensure_node(self, node_id: str):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "score": self.initial_score,
                "status": NodeStatus.ACTIVE,
                "history": [],
            }

    # -----------------------------------------------------------------
    # UPDATE FROM CONSENSUS RESULT
    # -----------------------------------------------------------------

    def update_from_proof(self, proof: Dict[str, Any]):
        """
        Update node reputation based on distributed proof.
        """

        final_hash = proof["final_result_hash"]

        for node in proof["nodes"]:
            node_id = node["node_id"]

            self._ensure_node(node_id)

            # ---------------------------------------------------------
            # AGREEMENT REWARD / PENALTY
            # ---------------------------------------------------------

            if node["result_hash"] == final_hash:
                self._reward(node_id, self.reward_agreement)
            else:
                self._penalize(node_id, self.penalty_mismatch, "result_mismatch")

            # ---------------------------------------------------------
            # REPLAY CHECK
            # ---------------------------------------------------------

            if node.get("replay_hash") != final_hash:
                self._penalize(node_id, self.penalty_replay_failure, "replay_mismatch")

            # ---------------------------------------------------------
            # SIGNATURE CHECK
            # ---------------------------------------------------------

            if not node.get("signature"):
                self._penalize(node_id, self.penalty_invalid_signature, "missing_signature")

            # ---------------------------------------------------------
            # STATUS UPDATE
            # ---------------------------------------------------------

            self._update_status(node_id)

    # -----------------------------------------------------------------
    # PENALTIES / REWARDS
    # -----------------------------------------------------------------

    def _penalize(self, node_id: str, amount: float, reason: str):
        self.nodes[node_id]["score"] -= amount

        self.nodes[node_id]["history"].append({
            "action": "penalty",
            "reason": reason,
            "delta": -amount,
        })

    def _reward(self, node_id: str, amount: float):
        self.nodes[node_id]["score"] += amount

        if self.nodes[node_id]["score"] > 1.0:
            self.nodes[node_id]["score"] = 1.0

        self.nodes[node_id]["history"].append({
            "action": "reward",
            "delta": amount,
        })

    # -----------------------------------------------------------------
    # STATUS TRANSITIONS
    # -----------------------------------------------------------------

    def _update_status(self, node_id: str):
        score = self.nodes[node_id]["score"]

        if score <= self.quarantine_threshold:
            self.nodes[node_id]["status"] = NodeStatus.QUARANTINED

        elif score <= self.watchlist_threshold:
            self.nodes[node_id]["status"] = NodeStatus.WATCHLIST

        else:
            self.nodes[node_id]["status"] = NodeStatus.ACTIVE

    # -----------------------------------------------------------------
    # FILTER NODES FOR CONSENSUS
    # -----------------------------------------------------------------

    def filter_active_nodes(self, node_ids: List[str]) -> List[str]:
        """
        Exclude quarantined nodes from consensus participation.
        """

        allowed = []

        for node_id in node_ids:
            self._ensure_node(node_id)

            if self.nodes[node_id]["status"] != NodeStatus.QUARANTINED:
                allowed.append(node_id)

        return allowed

    # -----------------------------------------------------------------
    # GET NODE STATUS
    # -----------------------------------------------------------------

    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        self._ensure_node(node_id)
        return self.nodes[node_id]

    # -----------------------------------------------------------------
    # SYSTEM SNAPSHOT (DETERMINISTIC)
    # -----------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            node_id: {
                "score": round(data["score"], 5),
                "status": data["status"],
            }
            for node_id, data in sorted(self.nodes.items())
        }
