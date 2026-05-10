# afritech/federation/economic_engine.py

"""
AfriTech Economic Engine

Purpose:
Provide staking, reward, and slashing mechanics for:

- nodes
- systems
- federated participants

Design Goals:
- deterministic behavior
- replay-safe accounting
- incentive alignment with truth
- integration with consensus proofs
"""

from typing import Dict, Any


class EconomicError(Exception):
    """Raised when economic operation fails"""
    pass


class EconomicEngine:
    """
    Economic incentive system

    Tracks:
    - stakes
    - rewards
    - penalties

    Enforces:
    - proportional rewards
    - deterministic slashing
    - economic accountability
    """

    def __init__(
        self,
        base_reward: float = 10.0,
        penalty_mismatch: float = 0.10,
        penalty_replay: float = 0.20,
        penalty_signature: float = 0.15,
        min_stake_required: float = 1.0,
    ):
        # Core ledgers
        self.stakes: Dict[str, float] = {}
        self.rewards: Dict[str, float] = {}
        self.penalties: Dict[str, float] = {}

        # Config
        self.base_reward = base_reward
        self.penalty_mismatch = penalty_mismatch
        self.penalty_replay = penalty_replay
        self.penalty_signature = penalty_signature
        self.min_stake_required = min_stake_required

    # -----------------------------------------------------------------
    # STAKING
    # -----------------------------------------------------------------

    def stake(self, participant_id: str, amount: float):
        if amount <= 0:
            raise EconomicError("invalid_stake_amount")

        self.stakes[participant_id] = self.get_stake(participant_id) + amount

    def get_stake(self, participant_id: str) -> float:
        return self.stakes.get(participant_id, 0.0)

    def require_min_stake(self, participant_id: str):
        if self.get_stake(participant_id) < self.min_stake_required:
            raise EconomicError(f"insufficient_stake: {participant_id}")

    # -----------------------------------------------------------------
    # REWARD SYSTEM
    # -----------------------------------------------------------------

    def reward(self, participant_id: str, amount: float):
        if amount <= 0:
            return

        self.rewards[participant_id] = self.rewards.get(participant_id, 0.0) + amount
        self.stakes[participant_id] = self.get_stake(participant_id) + amount

    def reward_weighted(self, participant_id: str, weight: float):
        """
        Reward proportional to stake weight.
        """
        stake = self.get_stake(participant_id)
        amount = self.base_reward * weight * (1 + stake)
        self.reward(participant_id, amount)

    # -----------------------------------------------------------------
    # SLASHING
    # -----------------------------------------------------------------

    def slash(self, participant_id: str, percent: float, reason: str):
        stake = self.get_stake(participant_id)

        if stake <= 0:
            return

        penalty = stake * percent

        self.stakes[participant_id] -= penalty

        if self.stakes[participant_id] < 0:
            self.stakes[participant_id] = 0

        self.penalties[participant_id] = self.penalties.get(participant_id, 0.0) + penalty

        # Log structured penalty event
        self._log_event(participant_id, "SLASH", reason, penalty)

    # -----------------------------------------------------------------
    # CONSENSUS APPLICATION (NODE LEVEL)
    # -----------------------------------------------------------------

    def apply_node_consensus(self, proof: Dict[str, Any]):
        """
        Apply rewards/slashing from node-level consensus proof.
        """

        for node in proof.get("nodes", []):

            node_id = node["node_id"]
            self.require_min_stake(node_id)

            if node["agrees"]:
                self.reward_weighted(node_id, weight=1.0)
            else:
                self.slash(node_id, self.penalty_mismatch, "result_mismatch")

            if node.get("replay_hash") != proof["final_result_hash"]:
                self.slash(node_id, self.penalty_replay, "replay_failure")

            if not node.get("signature"):
                self.slash(node_id, self.penalty_signature, "missing_signature")

    # -----------------------------------------------------------------
    # CONSENSUS APPLICATION (SYSTEM LEVEL - FEDERATION)
    # -----------------------------------------------------------------

    def apply_federation_consensus(self, federated_proof: Dict[str, Any]):
        """
        Apply system-level rewards/slashing.
        """

        for system in federated_proof.get("systems", []):

            system_id = system["system_id"]
            self.require_min_stake(system_id)

            if system["agrees"]:
                self.reward(system_id, self.base_reward * 2)
            else:
                self.slash(system_id, self.penalty_mismatch * 2, "federated_mismatch")

            if not system.get("signature"):
                self.slash(system_id, self.penalty_signature, "missing_signature")

    # -----------------------------------------------------------------
    # GOVERNANCE REWARDS
    # -----------------------------------------------------------------

    def apply_governance_vote(self, votes: Dict[str, bool], final_decision: bool):
        """
        Reward correct voters, penalize incorrect ones.
        """

        for node_id, vote in votes.items():

            self.require_min_stake(node_id)

            if vote == final_decision:
                self.reward(node_id, self.base_reward / 2)
            else:
                self.slash(node_id, self.penalty_mismatch, "governance_mismatch")

    # -----------------------------------------------------------------
    # HELPER: EVENT LOG (DETERMINISTIC)
    # -----------------------------------------------------------------

    def _log_event(self, participant_id: str, action: str, reason: str, amount: float):
        """
        Minimal deterministic log (extendable to audit system)
        """
        # NOTE: no timestamps (preserve determinism)
        pass

    # -----------------------------------------------------------------
    # SNAPSHOT (DETERMINISTIC STATE)
    # -----------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """
        Deterministic state snapshot
        """

        return {
            "stakes": self._sorted_dict(self.stakes),
            "rewards": self._sorted_dict(self.rewards),
            "penalties": self._sorted_dict(self.penalties),
        }

    def _sorted_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {k: round(v, 6) for k, v in sorted(data.items())}