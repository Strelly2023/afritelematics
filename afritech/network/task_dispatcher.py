"""
afritech/task_dispatcher.py

Distributed Task Dispatcher
===========================

Coordinates execution across:
- Local runtime
- Distributed nodes
- Consensus engine

Responsibilities:
- Route tasks (local vs distributed)
- Execute via consensus when required
- Handle failures gracefully
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

from network.node_registry import NodeRegistry
from network.node.http_node_client import HttpNodeClient
from network.consensus.distributed_consensus import DistributedConsensus


# -----------------------------------------------------------------
# DISPATCH ERROR
# -----------------------------------------------------------------

class TaskDispatchError(Exception):
    pass


# -----------------------------------------------------------------
# TASK DISPATCHER
# -----------------------------------------------------------------

class TaskDispatcher:

    def __init__(
        self,
        node_registry: NodeRegistry,
        local_executor_fn,
        consensus_threshold: float = 0.66,
        enable_distributed: bool = True,
    ):
        """
        :param node_registry: NodeRegistry instance
        :param local_executor_fn: fallback/local execution function
        :param consensus_threshold: required consensus ratio
        :param enable_distributed: enable/disable distributed execution
        """
        self.node_registry = node_registry
        self.local_executor_fn = local_executor_fn
        self.consensus_threshold = consensus_threshold
        self.enable_distributed = enable_distributed

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def dispatch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main dispatch method
        """

        if not isinstance(request, dict):
            raise TaskDispatchError("Request must be a dictionary")

        # -------------------------------------------------------------
        # ROUTING DECISION
        # -------------------------------------------------------------
        if self._should_use_distributed(request):
            return self._dispatch_distributed(request)

        return self._dispatch_local(request)

    # -----------------------------------------------------------------
    # ROUTING LOGIC
    # -----------------------------------------------------------------

    def _should_use_distributed(self, request: Dict[str, Any]) -> bool:
        """
        Decide whether to use distributed execution
        """

        if not self.enable_distributed:
            return False

        replay = request.get("replay_requirements", {})

        # Use distributed execution if explicitly required
        if replay.get("require_consensus"):
            return True

        # Also use distributed if multiple nodes available
        if len(self.node_registry.list_active()) > 1:
            return True

        return False

    # -----------------------------------------------------------------
    # LOCAL EXECUTION
    # -----------------------------------------------------------------

    def _dispatch_local(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute locally
        """

        try:
            result = self.local_executor_fn(request)

            if not isinstance(result, dict):
                raise TaskDispatchError("Local executor returned invalid result")

            return {
                "mode": "LOCAL",
                "result": result
            }

        except Exception as e:
            raise TaskDispatchError(f"Local execution failed: {str(e)}")

    # -----------------------------------------------------------------
    # DISTRIBUTED EXECUTION
    # -----------------------------------------------------------------

    def _dispatch_distributed(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute using distributed consensus
        """

        nodes = self._build_node_clients()

        if not nodes:
            raise TaskDispatchError("No available nodes for distributed execution")

        consensus_engine = DistributedConsensus(
            nodes,
            threshold_ratio=self.consensus_threshold
        )

        try:
            result = consensus_engine.execute_with_consensus(request)

            return {
                "mode": "DISTRIBUTED",
                "consensus": result["consensus"],
                "result": result["result"],
                "node_failures": result.get("node_failures", [])
            }

        except Exception as e:
            raise TaskDispatchError(f"Distributed execution failed: {str(e)}")

    # -----------------------------------------------------------------
    # BUILD NODE CLIENTS
    # -----------------------------------------------------------------

    def _build_node_clients(self) -> List[HttpNodeClient]:
        """
        Convert registry nodes → HttpNodeClients
        """

        clients = []

        for record in self.node_registry.get_consensus_nodes():

            node = record.identity
            metadata = node.metadata or {}

            base_url = metadata.get("url")

            if not base_url:
                continue  # skip nodes without endpoint

            client = HttpNodeClient(
                node_id=node.node_id,
                base_url=base_url
            )

            clients.append(client)

        return clients

    # -----------------------------------------------------------------
    # METRICS
    # -----------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """
        Dispatcher-level metrics
        """

        nodes = self.node_registry.stats()

        return {
            "distributed_enabled": self.enable_distributed,
            "consensus_threshold": self.consensus_threshold,
            "nodes": nodes
        }

    # -----------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"<TaskDispatcher distributed={self.enable_distributed} "
            f"nodes={self.node_registry.stats()}>"
        )