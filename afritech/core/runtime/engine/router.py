"""
afritech/runtime/engine/router.py

Execution Router
================

Routes execution requests to the appropriate execution path:
- Direct execution
- Distributed consensus execution
- Future: policy-based routing (risk/scoring)

Responsibilities:
- Determine execution path
- Maintain deterministic routing
- Integrate with execution + consensus layers
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from runtime.context.runtime_context import RuntimeContext
from afritech.core.runtime.engine.executor import ExecutionEngine
from afritech.core.runtime.engine.dispatch import DispatchResult


# -----------------------------------------------------------------
# ROUTER ERROR
# -----------------------------------------------------------------

class RouterError(Exception):
    pass


# -----------------------------------------------------------------
# ROUTER
# -----------------------------------------------------------------

class ExecutionRouter:

    def __init__(
        self,
        executor: ExecutionEngine,
        consensus_layer: Optional[Any] = None,
        event_bus: Optional[Any] = None,
    ):
        """
        :param executor: execution engine
        :param consensus_layer: distributed consensus engine
        :param event_bus: real-time event bus
        """
        self.executor = executor
        self.consensus_layer = consensus_layer
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN ROUTE FUNCTION
    # -----------------------------------------------------------------

    def route(self, context: RuntimeContext) -> DispatchResult:

        if not isinstance(context, RuntimeContext):
            raise RouterError("Invalid RuntimeContext")

        if not context.verify():
            raise RouterError("Context integrity failed")

        # -------------------------------------------------------------
        # Routing decision
        # -------------------------------------------------------------
        route_type = self._determine_route(context)

        self._emit({
            "type": "ROUTING_DECISION",
            "route": route_type,
            "context_hash": context.context_hash
        })

        # -------------------------------------------------------------
        # Execute according to route
        # -------------------------------------------------------------

        if route_type == "DIRECT_EXECUTION":
            return self._execute_direct(context)

        elif route_type == "CONSENSUS_EXECUTION":
            return self._execute_consensus(context)

        else:
            raise RouterError(f"Unknown route type: {route_type}")

    # -----------------------------------------------------------------
    # ROUTING STRATEGY
    # -----------------------------------------------------------------

    def _determine_route(self, context: RuntimeContext) -> str:
        """
        Deterministic routing logic

        Current strategy:
        - If replay_requirements demand distributed verification → consensus
        - Otherwise → direct execution
        """

        replay = context.replay_requirements or {}

        if replay.get("require_consensus") is True:
            return "CONSENSUS_EXECUTION"

        return "DIRECT_EXECUTION"

    # -----------------------------------------------------------------
    # DIRECT EXECUTION
    # -----------------------------------------------------------------

    def _execute_direct(self, context: RuntimeContext) -> DispatchResult:

        result = self.executor.execute(context)

        return DispatchResult(
            success=result.success,
            result=result.to_dict(),
            error=result.error,
            context=context
        )

    # -----------------------------------------------------------------
    # CONSENSUS EXECUTION
    # -----------------------------------------------------------------

    def _execute_consensus(self, context: RuntimeContext) -> DispatchResult:

        if not self.consensus_layer:
            raise RouterError("Consensus layer not configured")

        request = {
            "authority_profile": context.authority_profile,
            "payload": context.payload,
            "replay_requirements": context.replay_requirements,
        }

        output = self.consensus_layer.execute_with_consensus(request)

        return DispatchResult(
            success=True,
            result=output,
            context=context
        )

    # -----------------------------------------------------------------
    # EVENT EMITTER
    # -----------------------------------------------------------------

    def _emit(self, event: Dict[str, Any]):

        if not self.event_bus:
            return

        try:
            import asyncio
            asyncio.create_task(self.event_bus.publish(event))
        except Exception:
            pass  # never break execution
