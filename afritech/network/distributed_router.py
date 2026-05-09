"""ch/network/distributed_router.py

Distributed Router
==================

Decides execution strategy for a request.

Responsibilities:
- Route execution (local vs distributed)
- Integrate consensus engine
- Maintain deterministic routing decisions
- Provide unified execution interface
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from network.consensus_engine import ConsensusEngine


# -----------------------------------------------------------------
# ROUTER ERROR
# -----------------------------------------------------------------

class DistributedRouterError(Exception):
    pass


# -----------------------------------------------------------------
# ROUTER
# -----------------------------------------------------------------

class DistributedRouter:

    def __init__(
        self,
        consensus_engine: ConsensusEngine,
        local_executor_fn,
        enable_consensus: bool = True,
        default_mode: str = "AUTO"
    ):
        """
        :param consensus_engine: ConsensusEngine instance
        :param local_executor_fn: fallback/local execution
        :param enable_consensus: toggle distributed execution
        :param default_mode: AUTO | LOCAL | CONSENSUS
        """
        self.consensus_engine = consensus_engine
        self.local_executor_fn = local_executor_fn
        self.enable_consensus = enable_consensus
        self.default_mode = default_mode

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def route(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main routing function
        """

        if not isinstance(request, dict):
            raise DistributedRouterError("Invalid request format")

        mode = self._determine_mode(request)

        if mode == "LOCAL":
            return self._execute_local(request)

        if mode == "CONSENSUS":
            return self._execute_consensus(request)

        raise DistributedRouterError(f"Unknown execution mode: {mode}")

    # -----------------------------------------------------------------
    # ROUTING DECISION
    # -----------------------------------------------------------------

    def _determine_mode(self, request: Dict[str, Any]) -> str:
        """
        Determines execution mode:
        LOCAL | CONSENSUS
        """

        # Forced modes (highest precedence)
        forced_mode = request.get("execution_mode")
        if forced_mode in ("LOCAL", "CONSENSUS"):
            return forced_mode

        # Global disable
        if not self.enable_consensus:
            return "LOCAL"

        # Replay requirement → consensus
        replay = request.get("replay_requirements", {})
        if replay.get("require_consensus") is True:
            return "CONSENSUS"

        # Default system mode
        if self.default_mode == "LOCAL":
            return "LOCAL"

        if self.default_mode == "CONSENSUS":
            return "CONSENSUS"

        # AUTO mode (smart decision)
        if self._has_multiple_nodes():
            return "CONSENSUS"

        return "LOCAL"

    # -----------------------------------------------------------------
    # LOCAL EXECUTION
    # -----------------------------------------------------------------

    def _execute_local(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute locally
        """

        try:
            result = self.local_executor_fn(request)

            if not isinstance(result, dict):
                raise DistributedRouterError("Local execution returned invalid result")

            return {
                "mode": "LOCAL",
                "result": result
            }

        except Exception as e:
            raise DistributedRouterError(f"Local execution failed: {str(e)}")

    # -----------------------------------------------------------------
    # CONSENSUS EXECUTION
    # -----------------------------------------------------------------

    def _execute_consensus(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute via distributed consensus
        """

        try:
            result = self.consensus_engine.execute(request)

            return {
                "mode": "CONSENSUS",
                "consensus": result.get("consensus"),
                "result": result.get("result"),
                "node_failures": result.get("node_failures", [])
            }

        except Exception as e:
            raise DistributedRouterError(f"Consensus execution failed: {str(e)}")

    # -----------------------------------------------------------------
    # NODE AVAILABILITY CHECK
    # -----------------------------------------------------------------

    def _has_multiple_nodes(self) -> bool:
        """
        Check if multiple nodes are available
        """
        stats = self.consensus_engine.node_registry.stats()
        return stats.get("active", 0) > 1

    # -----------------------------------------------------------------
    # METRICS
    # -----------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        return {
            "enable_consensus": self.enable_consensus,
            "default_mode": self.default_mode,
            "node_stats": self.consensus_engine.node_registry.stats()
        }

    # -----------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"<DistributedRouter mode={self.default_mode} "
            f"consensus_enabled={self.enable_consensus}>"
        )
