# afritech/evaluation/replay_analysis/replay_analysis_engine.py

"""
AfriTech Replay Analysis Engine
===============================

Validates execution determinism by replaying execution
through the SAME constitutional execution kernel used at runtime.

CONSTITUTIONAL RULE:
- Replay MUST NOT execute directly.
- Replay MUST use kernel.EXECUTE().
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.engine.executor import ExecutionEngine, ExecutionResult
from afritech.runtime.kernel.execute import EXECUTE


# -----------------------------------------------------------------
# REPLAY ERROR
# -----------------------------------------------------------------

class ReplayAnalysisError(Exception):
    pass


# -----------------------------------------------------------------
# REPLAY RESULT
# -----------------------------------------------------------------

class ReplayAnalysisResult:
    """
    Result of a replay analysis comparison.
    """

    def __init__(
        self,
        *,
        valid: bool,
        original_hash: Optional[str],
        replay_hash: Optional[str],
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
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
            "timestamp": self.timestamp,
        }


# -----------------------------------------------------------------
# REPLAY ANALYSIS ENGINE
# -----------------------------------------------------------------

class ReplayAnalysisEngine:
    """
    Constitutional replay analysis engine.

    Replays execution via kernel.EXECUTE() and compares results
    against original execution artifacts.
    """

    def __init__(
        self,
        *,
        execution_engine: ExecutionEngine,
        event_bus: Optional[Any] = None,
    ):
        """
        :param execution_engine: ExecutionEngine (mechanism only)
        :param event_bus: optional telemetry / event streaming
        """
        self.execution_engine = execution_engine
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def analyze(
        self,
        *,
        context: RuntimeContext,
        original_result: ExecutionResult,
    ) -> ReplayAnalysisResult:
        """
        Perform deterministic replay and compare results.
        """

        if not isinstance(context, RuntimeContext):
            raise ReplayAnalysisError("Invalid RuntimeContext")

        if not isinstance(original_result, ExecutionResult):
            raise ReplayAnalysisError("Invalid ExecutionResult")

        if not context.verify():
            return self._fail(
                reason="Context integrity verification failed",
                original_hash=original_result.result_hash,
                replay_hash=None,
            )

        try:
            self._emit({
                "type": "REPLAY_STARTED",
                "context_hash": context.context_hash,
            })

            # ---------------------------------------------------------
            # REPLAY EXECUTION (KERNEL‑ENFORCED)
            # ---------------------------------------------------------

            replay_result: ExecutionResult = EXECUTE(
                engine=self.execution_engine,
                context=context,
            )

            if not replay_result.success:
                return self._fail(
                    reason="Replay execution failed",
                    original_hash=original_result.result_hash,
                    replay_hash=replay_result.result_hash,
                    details={
                        "error": replay_result.error,
                    },
                )

            # ---------------------------------------------------------
            # HASH COMPARISON (AUTHORITATIVE)
            # ---------------------------------------------------------

            if original_result.result_hash != replay_result.result_hash:
                return self._fail(
                    reason="REPLAY_DIVERGENCE",
                    original_hash=original_result.result_hash,
                    replay_hash=replay_result.result_hash,
                    details={
                        "original_output": original_result.output,
                        "replay_output": replay_result.output,
                    },
                )

            # ---------------------------------------------------------
            # SUCCESS
            # ---------------------------------------------------------

            self._emit({
                "type": "REPLAY_VALID",
                "context_hash": context.context_hash,
            })

            return ReplayAnalysisResult(
                valid=True,
                original_hash=original_result.result_hash,
                replay_hash=replay_result.result_hash,
            )

        except Exception as e:
            return self._fail(
                reason="Replay analysis error",
                original_hash=original_result.result_hash,
                replay_hash=None,
                details={
                    "exception": self._format_error(e),
                },
            )

    # -----------------------------------------------------------------
    # FAILURE HANDLER
    # -----------------------------------------------------------------

    def _fail(
        self,
        *,
        reason: str,
        original_hash: Optional[str],
        replay_hash: Optional[str],
        details: Optional[Dict[str, Any]] = None,
    ) -> ReplayAnalysisResult:

        self._emit({
            "type": "REPLAY_FAILED",
            "reason": reason,
        })

        return ReplayAnalysisResult(
            valid=False,
            original_hash=original_hash,
            replay_hash=replay_hash,
            reason=reason,
            details=details,
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

    def _emit(self, event: Dict[str, Any]) -> None:
        """
        Best‑effort event emission.
        Must NEVER affect replay validity.
        """

        if not self.event_bus:
            return

        try:
            import asyncio
            asyncio.create_task(self.event_bus.publish(event))
        except Exception:
            pass