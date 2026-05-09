"""
afritech/runtime/engine/verifier.py

Execution Verifier
==================

Validates execution results under constitutional guarantees.

Responsibilities:
- Verify result integrity (hash consistency)
- Enforce deterministic execution
- Provide hooks for drift detection
- Validate replay correctness
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import hashlib
import json

from runtime.engine.executor import ExecutionResult
from runtime.context.runtime_context import RuntimeContext


# -----------------------------------------------------------------
# VERIFIER ERROR
# -----------------------------------------------------------------

class VerificationError(Exception):
    pass


# -----------------------------------------------------------------
# VERIFICATION RESULT
# -----------------------------------------------------------------

class VerificationResult:

    def __init__(
        self,
        valid: bool,
        reason: Optional[str] = None,
        context: Optional[RuntimeContext] = None,
        result_hash: Optional[str] = None,
    ):
        self.valid = valid
        self.reason = reason
        self.context = context
        self.result_hash = result_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "context_hash": self.context.context_hash if self.context else None,
            "result_hash": self.result_hash,
        }


# -----------------------------------------------------------------
# VERIFIER ENGINE
# -----------------------------------------------------------------

class ExecutionVerifier:

    def __init__(self, event_bus: Optional[Any] = None):
        """
        :param event_bus: optional real-time event stream
        """
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN VERIFY ENTRYPOINT
    # -----------------------------------------------------------------

    def verify(
        self,
        execution_result: ExecutionResult
    ) -> VerificationResult:

        if not isinstance(execution_result, ExecutionResult):
            raise VerificationError("Invalid ExecutionResult")

        context = execution_result.context

        if context and not context.verify():
            return self._fail("Context integrity failure", context, execution_result)

        if not execution_result.verify():
            return self._fail("Result hash mismatch", context, execution_result)

        # Optional deeper deterministic validation
        deterministic_check = self._check_determinism(execution_result)

        if not deterministic_check["valid"]:
            return self._fail(
                deterministic_check["reason"],
                context,
                execution_result
            )

        self._emit({
            "type": "VERIFICATION_PASSED",
            "context_hash": context.context_hash if context else None
        })

        return VerificationResult(
            valid=True,
            context=context,
            result_hash=execution_result.result_hash
        )

    # -----------------------------------------------------------------
    # DETERMINISM CHECK
    # -----------------------------------------------------------------

    def _check_determinism(
        self,
        execution_result: ExecutionResult
    ) -> Dict[str, Any]:
        """
        Basic determinism check.

        Future expansion:
        - replay execution
        - drift engine integration
        """

        output = execution_result.output

        if output is None:
            return {"valid": False, "reason": "Missing output"}

        try:
            # Ensure canonical serialization (no non-deterministic objects)
            json.dumps(output, sort_keys=True)
        except Exception:
            return {"valid": False, "reason": "Non-serializable output"}

        return {"valid": True}

    # -----------------------------------------------------------------
    # FAILURE HANDLER
    # -----------------------------------------------------------------

    def _fail(
        self,
        reason: str,
        context: Optional[RuntimeContext],
        result: ExecutionResult
    ) -> VerificationResult:

        self._emit({
            "type": "VERIFICATION_FAILED",
            "reason": reason,
            "context_hash": context.context_hash if context else None
        })

        return VerificationResult(
            valid=False,
            reason=reason,
            context=context,
            result_hash=result.result_hash
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
            pass