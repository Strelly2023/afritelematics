# afritech/civilization/civilization_engine.py

"""
AfriTech Civilization Engine

Top-Level Autonomous System Orchestrator

Responsibilities:
- Execute deterministic computation
- Verify via replay and distributed consensus
- Validate across federation
- Update trust and incentives
- Heal failures
- Evolve governance

This engine represents the full civilization-scale intelligence loop.
"""

from typing import Dict, Any


class CivilizationError(Exception):
    """Raised when system-level orchestration fails"""
    pass


class CivilizationEngine:
    """
    Full AfriTech civilization orchestration engine.

    Integrates:
    - ExecutionEngine
    - DistributedVerifier
    - FederationVerifier
    - NodeReputationManager
    - EconomicEngine
    - SelfHealingEngine
    - AutonomousGovernanceEngine
    """

    def __init__(
        self,
        execution_engine,
        distributed_verifier,
        federation_verifier,
        reputation_manager,
        economic_engine,
        healing_engine,
        governance_engine,
    ):
        self.execution = execution_engine
        self.distributed_verifier = distributed_verifier
        self.federation_verifier = federation_verifier
        self.reputation = reputation_manager
        self.economics = economic_engine
        self.healing = healing_engine
        self.governance = governance_engine

    # -----------------------------------------------------------------
    # MAIN PROCESS
    # -----------------------------------------------------------------

    def process(self, context) -> Dict[str, Any]:
        """
        Full civilization execution pipeline.

        Steps:
        1. Execute
        2. Distributed verification
        3. Federated verification
        4. Update reputation
        5. Apply economic logic
        6. Heal system if needed
        7. Evolve governance

        Returns:
            structured system state
        """

        # -------------------------------------------------------------
        # STEP 1 — EXECUTION
        # -------------------------------------------------------------
        execution_result = self._execute(context)

        # -------------------------------------------------------------
        # STEP 2 — DISTRIBUTED CONSENSUS
        # -------------------------------------------------------------
        distributed_proof = self._distributed_verify(execution_result)

        # -------------------------------------------------------------
        # STEP 3 — FEDERATION CONSENSUS
        # -------------------------------------------------------------
        federated_proof = self._federated_verify(distributed_proof)

        # -------------------------------------------------------------
        # STEP 4 — UPDATE REPUTATION
        # -------------------------------------------------------------
        self.reputation.update_from_proof(distributed_proof)

        # -------------------------------------------------------------
        # STEP 5 — APPLY ECONOMICS
        # -------------------------------------------------------------
        self.economics.apply_node_consensus(distributed_proof)

        if federated_proof:
            self.economics.apply_federation_consensus(federated_proof)

        # -------------------------------------------------------------
        # STEP 6 — SELF-HEALING
        # -------------------------------------------------------------
        healing_result = self.healing.process(
            distributed_proof.get("nodes", [])
        )

        # -------------------------------------------------------------
        # STEP 7 — GOVERNANCE EVOLUTION
        # -------------------------------------------------------------
        governance_result = self.governance.evolve(
            self._build_system_metrics(distributed_proof)
        )

        # -------------------------------------------------------------
        # FINAL STATE
        # -------------------------------------------------------------
        return {
            "execution": execution_result.to_dict(),
            "distributed_proof": distributed_proof,
            "federated_proof": federated_proof,
            "healing": healing_result,
            "governance": governance_result,
            "reputation": self.reputation.snapshot(),
            "economics": self.economics.snapshot(),
        }

    # -----------------------------------------------------------------
    # EXECUTION
    # -----------------------------------------------------------------

    def _execute(self, context):
        result = self.execution.execute(context)

        if not result.verify():
            raise CivilizationError("execution_result_integrity_failed")

        return result

    # -----------------------------------------------------------------
    # DISTRIBUTED VERIFICATION
    # -----------------------------------------------------------------

    def _distributed_verify(self, execution_result) -> Dict[str, Any]:
        """
        Build synthetic node results from execution.

        In production:
        - collected from multiple nodes
        """

        node_results = self._build_node_results(execution_result)

        proof = self.distributed_verifier.verify(node_results)

        return proof

    # -----------------------------------------------------------------
    # FEDERATION VERIFICATION
    # -----------------------------------------------------------------

    def _federated_verify(self, distributed_proof) -> Dict[str, Any] | None:
        """
        In production:
        - results received from multiple systems
        """

        try:
            system_results = self._build_system_results(distributed_proof)

            return self.federation_verifier.verify(system_results)

        except Exception:
            return None  # federation optional / failure tolerated

    # -----------------------------------------------------------------
    # NODE RESULT BUILDER (DETERMINISTIC)
    # -----------------------------------------------------------------

    def _build_node_results(self, execution_result) -> list:
        """
        Deterministic placeholder

        In production:
        - gather from real nodes
        """

        base_hash = execution_result.result_hash
        context_hash = execution_result.context.context_hash

        return [
            {
                "node_id": "NODE_A",
                "context_hash": context_hash,
                "result_hash": base_hash,
                "replay_hash": base_hash,
                "signature": "SIG_A",
            },
            {
                "node_id": "NODE_B",
                "context_hash": context_hash,
                "result_hash": base_hash,
                "replay_hash": base_hash,
                "signature": "SIG_B",
            },
            {
                "node_id": "NODE_C",
                "context_hash": context_hash,
                "result_hash": base_hash,
                "replay_hash": base_hash,
                "signature": "SIG_C",
            },
        ]

    # -----------------------------------------------------------------
    # SYSTEM RESULT BUILDER
    # -----------------------------------------------------------------

    def _build_system_results(self, distributed_proof) -> list:
        """
        Deterministic placeholder

        In production:
        - gathered from multiple systems
        """

        result_hash = distributed_proof["final_result_hash"]
        context_hash = distributed_proof["context_hash"]

        return [
            {
                "system_id": "SYS_A",
                "context_hash": context_hash,
                "result_hash": result_hash,
                "proof_hash": result_hash,
                "signature": "SYS_SIG_A",
            },
            {
                "system_id": "SYS_B",
                "context_hash": context_hash,
                "result_hash": result_hash,
                "proof_hash": result_hash,
                "signature": "SYS_SIG_B",
            },
            {
                "system_id": "SYS_C",
                "context_hash": context_hash,
                "result_hash": result_hash,
                "proof_hash": result_hash,
                "signature": "SYS_SIG_C",
            },
        ]

    # -----------------------------------------------------------------
    # SYSTEM METRICS (FOR GOVERNANCE)
    # -----------------------------------------------------------------

    def _build_system_metrics(self, distributed_proof) -> Dict[str, Any]:
        """
        Deterministic metrics for governance decisions
        """

        disagreement_count = len(distributed_proof.get("disagreeing_nodes", []))
        total_nodes = distributed_proof.get("node_count", 1)

        failure_rate = disagreement_count / total_nodes

        return {
            "failure_rate": round(failure_rate, 5),
            "agreement_ratio": distributed_proof.get("agreement_ratio"),
        }
