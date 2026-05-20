"""
afritech/runtime/engine/dispatch.py

Execution Dispatch Layer
=======================

Coordinates execution flow between:
- RuntimeContext
- Execution function
- Consensus layer (optional)
- Validation + governance layers

Responsibilities:
- Normalize execution input
- Invoke execution engine
- Enforce deterministic structure
- Emit structured execution results
"""

from __future__ import annotations

from typing import Dict, Any, Callable, Optional
from datetime import datetime
import traceback

from runtime.context.runtime_context import RuntimeContext


# -----------------------------------------------------------------
# DISPATCH ERROR
# -----------------------------------------------------------------

class DispatchError(Exception):
    pass


# -----------------------------------------------------------------
# DISPATCH RESULT
# -----------------------------------------------------------------

class DispatchResult:

    def __init__(
        self,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        context: Optional[RuntimeContext] = None
    ):
        self.success = success
        self.result = result
        self.error = error
        self.context = context

        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "context": self.context.to_dict() if self.context else None,
            "timestamp": self.timestamp,
        }


# -----------------------------------------------------------------
# DISPATCH ENGINE
# -----------------------------------------------------------------

class ExecutionDispatcher:

    def __init__(
        self,
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        consensus_layer: Optional[Any] = None,
        event_bus: Optional[Any] = None
    ):
        """
        :param execution_fn: deterministic execution function
        :param consensus_layer: optional distributed consensus engine
        :param event_bus: optional real-time event emitter
        """
        self.execution_fn = execution_fn
        self.consensus_layer = consensus_layer
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def dispatch(self, request: Dict[str, Any]) -> DispatchResult:
        """
        Main execution entrypoint
        """

        try:
            context = RuntimeContext(
                authority_profile=request.get("authority_profile", "unknown"),
                payload=request.get("payload", {}),
                replay_requirements=request.get("replay_requirements", {}),
            )

            # Emit start event
            self._emit({
                "type": "EXECUTION_STARTED",
                "context_hash": context.context_hash
            })

            # ---------------------------------------------------------
            # Execute
            # ---------------------------------------------------------
            if self.consensus_layer:
                execution_output = self.consensus_layer.execute_with_consensus(request)
            else:
                execution_output = self.execution_fn(request)

            # Emit success
            self._emit({
                "type": "EXECUTION_COMPLETED",
                "context_hash": context.context_hash
            })

            return DispatchResult(
                success=True,
                result=execution_output,
                context=context
            )

        except Exception as e:

            # Emit failure
            self._emit({
                "type": "EXECUTION_FAILED",
                "error": str(e)
            })

            return DispatchResult(
                success=False,
                error=self._format_error(e),
                context=None
            )

    # -----------------------------------------------------------------
    # ERROR FORMATTER
    # -----------------------------------------------------------------

    def _format_error(self, e: Exception) -> str:
        return "".join(traceback.format_exception_only(type(e), e)).strip()

    # -----------------------------------------------------------------
    # EVENT EMITTER
    # -----------------------------------------------------------------

    def _emit(self, event: Dict[str, Any]) -> None:
        if not self.event_bus:
            return

        try:
            import asyncio
            asyncio.create_task(self.event_bus.publish(event))
        except Exception:
            # Never break execution due to telemetry failure
            pass