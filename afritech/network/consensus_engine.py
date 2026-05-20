"""
afritech/network/consensus_engine.py

Consensus Engine (System-Level Orchestrator)
============================================

Coordinates distributed consensus execution across nodes.

Responsibilities:
- Select healthy nodes from registry
- Build node clients (HTTP/local)
- Execute distributed consensus
- Validate results (hash + proof + zk proof)
- Handle consensus failures and fallback
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from network.node_registry import NodeRegistry
from network.node.http_node_client import HttpNodeClient
from network.consensus.distributed_consensus import (
    DistributedConsensus,
    ConsensusError,
)

# ✅ Proof + ZK validation
from afritech.zk.interface import ZKProof
from afritech.zk.registry import ZKRegistry
from afritech.core.runtime.guards.proof_validator import ProofValidator


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class ConsensusEngineError(Exception):
    pass


# -----------------------------------------------------------------
# ENGINE
# -----------------------------------------------------------------

class ConsensusEngine:

    def __init__(
        self,
        node_registry: NodeRegistry,
        threshold_ratio: float = 0.66,
        timeout: float = 5.0,
        enable_fallback: bool = True,
        local_executor_fn=None,
        require_proof: bool = True,
        require_zk: bool = False,
    ):
        self.node_registry = node_registry
        self.threshold_ratio = threshold_ratio
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        self.local_executor_fn = local_executor_fn

        # ✅ enforcement flags
        self.require_proof = require_proof
        self.require_zk = require_zk

    # -----------------------------------------------------------------
    # MAIN EXECUTION
    # -----------------------------------------------------------------

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:

        nodes = self._build_node_clients()

        if not nodes:
            if self.enable_fallback:
                return self._fallback_execute(request)
            raise ConsensusEngineError("no_available_nodes")

        consensus = DistributedConsensus(
            nodes,
            threshold_ratio=self.threshold_ratio,
        )

        try:
            result = consensus.execute_with_consensus(request)

            validated_result = self._validate_result(result)

            return {
                "mode": "CONSENSUS",
                "consensus": result["consensus"],
                "result": validated_result,
                "node_failures": result.get("node_failures", []),
            }

        except ConsensusError as e:

            if self.enable_fallback:
                fallback = self._fallback_execute(request)

                return {
                    "mode": "FALLBACK",
                    "error": str(e),
                    "fallback": fallback,
                }

            raise ConsensusEngineError(str(e))

    # -----------------------------------------------------------------
    # RESULT VALIDATION (CRITICAL)
    # -----------------------------------------------------------------

    def _validate_result(self, consensus_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforces:
        - result_hash presence
        - proof validation
        - zk proof validation
        """

        result = consensus_result.get("result")

        if not isinstance(result, dict):
            raise ConsensusEngineError("invalid_result_structure")

        if "result_hash" not in result:
            raise ConsensusEngineError("missing_result_hash")

        # ---------------------------------------------------------
        # PROOF VALIDATION
        # ---------------------------------------------------------
        proof = result.get("proof")

        if self.require_proof:
            if not proof:
                raise ConsensusEngineError("missing_proof")

            try:
                ProofValidator.validate(proof)
            except Exception as e:
                raise ConsensusEngineError(f"invalid_proof: {str(e)}")

        # ---------------------------------------------------------
        # ZK VALIDATION
        # ---------------------------------------------------------
        zk_data = result.get("zk_proof")

        if self.require_zk:
            if not zk_data:
                raise ConsensusEngineError("missing_zk_proof")

        if zk_data:
            try:
                zk_proof = ZKProof.from_dict(zk_data)

                if not ZKRegistry.verify(zk_proof):
                    raise ConsensusEngineError("invalid_zk_proof")

            except Exception as e:
                raise ConsensusEngineError(f"zk_verification_failed: {str(e)}")

        return result

    # -----------------------------------------------------------------
    # NODE BUILDER
    # -----------------------------------------------------------------

    def _build_node_clients(self) -> List[HttpNodeClient]:

        clients = []

        for record in self.node_registry.get_consensus_nodes():

            identity = record.identity
            metadata = identity.metadata or {}
            url = metadata.get("url")

            if not url:
                continue

            clients.append(
                HttpNodeClient(
                    node_id=identity.node_id,
                    base_url=url,
                    timeout=self.timeout,
                )
            )

        return clients

    # -----------------------------------------------------------------
    # FALLBACK EXECUTION
    # -----------------------------------------------------------------

    def _fallback_execute(self, request: Dict[str, Any]) -> Dict[str, Any]:

        if not self.local_executor_fn:
            raise ConsensusEngineError("no_fallback_executor")

        try:
            result = self.local_executor_fn(request)

            if not isinstance(result, dict):
                raise ConsensusEngineError("invalid_fallback_result")

            return result

        except Exception as e:
            raise ConsensusEngineError(f"fallback_failed: {str(e)}")

    # -----------------------------------------------------------------
    # STATS
    # -----------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        return {
            "threshold_ratio": self.threshold_ratio,
            "timeout": self.timeout,
            "fallback_enabled": self.enable_fallback,
            "require_proof": self.require_proof,
            "require_zk": self.require_zk,
            "nodes": self.node_registry.stats(),
        }

    # -----------------------------------------------------------------
    # REPR
    # -----------------------------------------------------------------

    def __repr__(self):
        stats = self.node_registry.stats()

        return (
            f"<ConsensusEngine threshold={self.threshold_ratio} "
            f"nodes={stats.get('total')} "
            f"require_zk={self.require_zk}>"
        )