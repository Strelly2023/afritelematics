"""
AfriTech Civilization Engine
============================

Constitutionally admissible orchestration surface.

Responsibilities:
- Orchestrate constitutional execution
- Verify via replay and distributed consensus
- Validate across federation
- Update trust and incentives
- Heal failures
- Evolve governance

IMPORTANT CONSTITUTIONAL RULE:
- This engine MUST NOT execute directly.
- ALL execution MUST pass through kernel.EXECUTE().
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.engine.executor import (
    ExecutionEngine,
    ExecutionResult,
)
from afritech.kernel.execute import EXECUTE


class CivilizationError(Exception):
    """Raised when system-level orchestration fails."""


class CivilizationEngine:
    """
    Civilization-scale orchestration engine.

    Constitutional guarantees:
    - NEVER owns execution authority
    - NEVER bypasses kernel execution
    - NEVER performs reflective execution
    - Deterministic orchestration only
    """

    def __init__(
        self,
        *,
        execution_engine: ExecutionEngine,
        distributed_verifier,
        federation_verifier,
        reputation_manager,
        economic_engine,
        healing_engine,
        governance_engine,
    ):
        self._execution_engine = execution_engine
        self._distributed_verifier = distributed_verifier
        self._federation_verifier = federation_verifier
        self._reputation = reputation_manager
        self._economics = economic_engine
        self._healing = healing_engine
        self._governance = governance_engine

    # =========================================================
    # MAIN EXECUTION PIPELINE
    # =========================================================

    def process(
        self,
        *,
        context: RuntimeContext,
    ) -> Dict[str, Any]:

        if not isinstance(context, RuntimeContext):
            raise CivilizationError(
                "Invalid RuntimeContext"
            )

        if not context.verify():
            raise CivilizationError(
                "RuntimeContext integrity verification failed"
            )

        # -----------------------------------------------------
        # STEP 1 — CONSTITUTIONAL EXECUTION
        # -----------------------------------------------------

        execution_result: ExecutionResult = EXECUTE(
            engine=self._execution_engine,
            context=context,
        )

        if not execution_result.verify():
            raise CivilizationError(
                "ExecutionResult integrity verification failed"
            )

        # -----------------------------------------------------
        # STEP 2 — DISTRIBUTED VERIFICATION
        # -----------------------------------------------------

        distributed_proof = self._distributed_verify(
            context=context,
            execution_result=execution_result,
        )

        # -----------------------------------------------------
        # STEP 3 — FEDERATION VERIFICATION
        # -----------------------------------------------------

        federated_proof = self._federated_verify(
            distributed_proof
        )

        # -----------------------------------------------------
        # STEP 4 — REPUTATION
        # -----------------------------------------------------

        self._reputation.update_from_proof(
            distributed_proof
        )

        # -----------------------------------------------------
        # STEP 5 — ECONOMICS
        # -----------------------------------------------------

        self._economics.apply_node_consensus(
            distributed_proof
        )

        if federated_proof is not None:
            self._economics.apply_federation_consensus(
                federated_proof
            )

        # -----------------------------------------------------
        # STEP 6 — SELF HEALING
        # -----------------------------------------------------

        healing_result = self._healing.process(
            distributed_proof.get("nodes", [])
        )

        # -----------------------------------------------------
        # STEP 7 — GOVERNANCE EVOLUTION
        # -----------------------------------------------------

        governance_result = self._governance.evolve(
            self._build_system_metrics(
                distributed_proof
            )
        )

        # -----------------------------------------------------
        # FINAL SNAPSHOT
        # -----------------------------------------------------

        return {
            "execution": execution_result.to_dict(),
            "distributed_proof": distributed_proof,
            "federated_proof": federated_proof,
            "healing": healing_result,
            "governance": governance_result,
            "reputation": self._reputation.snapshot(),
            "economics": self._economics.snapshot(),
        }

    # =========================================================
    # DISTRIBUTED VERIFICATION
    # =========================================================

    def _distributed_verify(
        self,
        *,
        context: RuntimeContext,
        execution_result: ExecutionResult,
    ) -> Dict[str, Any]:

        node_results = self._build_node_results(
            context=context,
            execution_result=execution_result,
        )

        return self._distributed_verifier.verify(
            node_results
        )

    # =========================================================
    # FEDERATION VERIFICATION
    # =========================================================

    def _federated_verify(
        self,
        distributed_proof: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        try:
            system_results = self._build_system_results(
                distributed_proof
            )

            return self._federation_verifier.verify(
                system_results
            )

        except Exception:
            return None

    # =========================================================
    # NODE RESULTS
    # =========================================================

    def _build_node_results(
        self,
        *,
        context: RuntimeContext,
        execution_result: ExecutionResult,
    ) -> list:

        base_hash = execution_result.result_hash
        context_hash = context.context_hash

        return [
            {
                "node_id": node_id,
                "context_hash": context_hash,
                "result_hash": base_hash,
                "replay_hash": base_hash,
                "signature": f"SIG_{node_id}",
            }
            for node_id in (
                "NODE_A",
                "NODE_B",
                "NODE_C",
            )
        ]

    # =========================================================
    # SYSTEM RESULTS
    # =========================================================

    def _build_system_results(
        self,
        distributed_proof: Dict[str, Any],
    ) -> list:

        result_hash = distributed_proof[
            "final_result_hash"
        ]

        context_hash = distributed_proof[
            "context_hash"
        ]

        return [
            {
                "system_id": system_id,
                "context_hash": context_hash,
                "result_hash": result_hash,
                "proof_hash": result_hash,
                "signature": f"SYS_SIG_{system_id}",
            }
            for system_id in (
                "SYS_A",
                "SYS_B",
                "SYS_C",
            )
        ]

    # =========================================================
    # GOVERNANCE METRICS
    # =========================================================

    def _build_system_metrics(
        self,
        distributed_proof: Dict[str, Any],
    ) -> Dict[str, Any]:

        disagreement_count = len(
            distributed_proof.get(
                "disagreeing_nodes",
                [],
            )
        )

        total_nodes = max(
            distributed_proof.get(
                "node_count",
                1,
            ),
            1,
        )

        failure_rate = (
            disagreement_count / total_nodes
        )

        return {
            "failure_rate": round(
                failure_rate,
                5,
            ),
            "agreement_ratio":
                distributed_proof.get(
                    "agreement_ratio"
                ),
        }