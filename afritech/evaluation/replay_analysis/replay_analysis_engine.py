"""
afritech/evaluation/replay_analysis/replay_analysis_engine.py

Replay Analysis Engine
======================

Validates execution determinism by replaying execution and comparing results.

Responsibilities:
- Re-execute workloads deterministically
- Compare outputs against original execution
- Detect replay divergence (drift/anomalies)
- Provide replay validation reports
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import traceback

from runtime.context.runtime_context import RuntimeContext
from runtime.engine.executor import ExecutionEngine, ExecutionResult


# -----------------------------------------------------------------
# REPLAY ERROR
# -----------------------------------------------------------------

class ReplayAnalysisError(Exception):
    pass


# -----------------------------------------------------------------
# REPLAY RESULT
# -----------------------------------------------------------------

class ReplayAnalysisResult:

    def __init__(
        self,
        valid: bool,
        original_hash: str,
        replay_hash: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.valid = valid
        self.original_hash = original_hash
        self.replay_hash = replay_hash
        self.reason = reason
        self.details = details or {}

        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "original_hash": self.original_hash,
            "replay_hash": self.replay_hash,
            "reason": self.reason,
            "details": self.details,
            "timestamp": self.timestamp
        }


# -----------------------------------------------------------------
# REPLAY ENGINE
# -----------------------------------------------------------------

class ReplayAnalysisEngine:

    def __init__(
        self,
        execution_engine: ExecutionEngine,
        event_bus: Optional[Any] = None
    ):
        """
        :param execution_engine: core execution engine
        :param event_bus: optional telemetry / event streaming
        """
        self.execution_engine = execution_engine
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def analyze(
        self,
        context: RuntimeContext,
        original_result: ExecutionResult
    ) -> ReplayAnalysisResult:
        """
        Perform replay and compare results
        """

        if not isinstance(context, RuntimeContext):
            raise ReplayAnalysisError("Invalid RuntimeContext")

        if not isinstance(original_result, ExecutionResult):
            raise ReplayAnalysisError("Invalid ExecutionResult")

        if not context.verify():
            return self._fail(
                "Context integrity failed",
                original_result.result_hash,
                None
            )

        try:
            self._emit({
                "type": "REPLAY_STARTED",
                "context_hash": context.context_hash
            })

            # ---------------------------------------------------------
            # Re-execution
            # ---------------------------------------------------------
            replay_result = self.execution_engine.execute(context)

            if not replay_result.success:
                return self._fail(
                    "Replay execution failed",
                    original_result.result_hash,
                    replay_result.result_hash,
                    {"error": replay_result.error}
                )

            # ---------------------------------------------------------
            # Compare hashes
            # ---------------------------------------------------------
            if original_result.result_hash != replay_result.result_hash:
                return self._fail(
                    "REPLAY_DIVERGENCE",
                    original_result.result_hash,
                    replay_result.result_hash,
                    {
                        "original": original_result.output,
                        "replay": replay_result.output
                    }
                )

            # ---------------------------------------------------------
            # Success
            # ---------------------------------------------------------
            self._emit({
                "type": "REPLAY_VALID",
                "context_hash": context.context_hash
            })

            return ReplayAnalysisResult(
                valid=True,
                original_hash=original_result.result_hash,
                replay_hash=replay_result.result_hash
            )

        except Exception as e:
            return self._fail(
                "Replay analysis error",
                original_result.result_hash,
                None,
                {
                    "exception": self._format_error(e)
                }
            )

    # -----------------------------------------------------------------
    # FAILURE HANDLER
    # -----------------------------------------------------------------

    def _fail(
        self,
        reason: str,
        original_hash: Optional[str],
        replay_hash: Optional[str],
        details: Optional[Dict[str, Any]] = None
    ) -> ReplayAnalysisResult:

        self._emit({
            "type": "REPLAY_FAILED",
            "reason": reason
        })

        return ReplayAnalysisResult(
            valid=False,
            original_hash=original_hash,
            replay_hash=replay_hash,
            reason=reason,
            details=details
        )

    # -----------------------------------------------------------------
    # ERROR FORMATTER
    # -----------------------------------------------------------------

    def _format_error(self, e: Exception) -> str:
        return "".join(
            traceback.format_exception_only(type(e), e)
        ).strip()

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
            pass
