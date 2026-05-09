# afritech/distributed/self_healing_engine.py

"""
AfriTech Self-Healing Distributed Governance Engine

Purpose:
Provide autonomous recovery for distributed execution by:

- detecting consensus failures
- isolating faulty nodes
- recomputing consensus
- restoring valid system state

This engine is deterministic and replay-safe.
"""

from typing import List, Dict, Any, Optional


class SelfHealingError(Exception):
    """Raised when healing process fails irrecoverably"""
    pass


class HealingStatus:
    HEALTHY = "HEALTHY"
    HEALED = "HEALED"
    DEGRADED = "DEGRADED"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"
    UNRECOVERABLE = "UNRECOVERABLE"


class SelfHealingEngine:
    """
    Self-healing governance engine.

    Integrates:
    - DistributedVerifier
    - NodeReputationManager

    Guarantees:
    - deterministic recovery flow
    - safe quorum reduction
    - controlled state repair
    """

    def __init__(
        self,
        verifier,
        reputation_manager,
        min_nodes: int = 2,
        enable_reseal: bool = True,
    ):
        self.verifier = verifier
        self.reputation = reputation_manager
        self.min_nodes = min_nodes
        self.enable_reseal = enable_reseal

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def process(self, node_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute distributed verification + healing.

        Returns structured status object.
        """

        try:
            proof = self.verifier.verify(node_results)

            # ✅ update reputation after success
            self.reputation.update_from_proof(proof)

            return self._build_response(
                status=HealingStatus.HEALTHY,
                proof=proof,
                message="Consensus successful",
            )

        except Exception as e:

            # 🚨 Initial consensus failure triggers healing
            return self._heal(node_results, str(e))

    # -----------------------------------------------------------------
    # HEALING CORE
    # -----------------------------------------------------------------

    def _heal(self, node_results: List[Dict[str, Any]], error: str) -> Dict[str, Any]:
        """
        Healing logic after consensus failure.
        """

        # ---------------------------------------------------------
        # STEP 1: Identify active nodes
        # ---------------------------------------------------------
        all_nodes = [n["node_id"] for n in node_results]
        active_node_ids = self.reputation.filter_active_nodes(all_nodes)

        filtered_results = [
            n for n in node_results if n["node_id"] in active_node_ids
        ]

        if len(filtered_results) < self.min_nodes:
            return self._build_response(
                status=HealingStatus.SYSTEM_FAILURE,
                message="Insufficient trusted nodes for recovery",
                details={"initial_error": error},
            )

        # ---------------------------------------------------------
        # STEP 2: Attempt consensus with filtered nodes
        # ---------------------------------------------------------
        try:
            proof = self.verifier.verify(filtered_results)

            # ✅ update reputation again after recovery success
            self.reputation.update_from_proof(proof)

            # -----------------------------------------------------
            # STEP 3: Optional resealing
            # -----------------------------------------------------
            reseal_info = None
            if self.enable_reseal:
                reseal_info = self._attempt_reseal(proof)

            return self._build_response(
                status=HealingStatus.HEALED,
                proof=proof,
                message="Consensus restored after filtering faulty nodes",
                details={
                    "initial_error": error,
                    "active_nodes": active_node_ids,
                    "reseal": reseal_info,
                },
            )

        except Exception as second_error:

            # ---------------------------------------------------------
            # STEP 3: Secondary failure → degrade system
            # ---------------------------------------------------------
            if len(filtered_results) >= self.min_nodes:
                return self._build_response(
                    status=HealingStatus.DEGRADED,
                    message="Partial recovery failed but nodes remain",
                    details={
                        "initial_error": error,
                        "secondary_error": str(second_error),
                        "remaining_nodes": active_node_ids,
                    },
                )

            return self._build_response(
                status=HealingStatus.UNRECOVERABLE,
                message="Consensus could not be restored",
                details={
                    "initial_error": error,
                    "secondary_error": str(second_error),
                },
            )

    # -----------------------------------------------------------------
    # RESEALING (CONSTITUTIONAL EVOLUTION)
    # -----------------------------------------------------------------

    def _attempt_reseal(self, proof: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Simulate resealing logic.

        In full system this would:
        - increment epoch
        - generate new attestation
        - issue new certificate
        """

        # NOTE: deterministic placeholder
        return {
            "resealed": True,
            "new_epoch_required": True,
            "trigger": "NODE_SET_CHANGED",
            "consensus_hash": proof["final_result_hash"],
        }

    # -----------------------------------------------------------------
    # RESPONSE BUILDER
    # -----------------------------------------------------------------

    def _build_response(
        self,
        status: str,
        proof: Optional[Dict[str, Any]] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return {
            "status": status,
            "message": message,
            "proof": proof,
            "details": details or {},
            "reputation_snapshot": self.reputation.snapshot(),
        }