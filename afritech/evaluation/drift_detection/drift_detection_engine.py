"""
afritech/evaluation/drift_detection/drift_detection_engine.py

Drift Detection Engine
======================

Detects execution drift and anomalies beyond simple replay checks.

Responsibilities:
- Identify divergence between expected and actual outputs
- Detect semantic inconsistencies
- Classify drift severity
- Trigger governance workflows
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

#from runtime.engine.executor import ExecutionResult
from afritech.shared.types import ExecutionResult
from afritech.shared.context import RuntimeContext



# -----------------------------------------------------------------
# DRIFT ERROR
# -----------------------------------------------------------------

class DriftDetectionError(Exception):
    def __init__(self, message: str, report: Optional[Any] = None):
        super().__init__(message)
        self.report = report


# -----------------------------------------------------------------
# DRIFT REPORT
# -----------------------------------------------------------------

class DriftReport:

    def __init__(
        self,
        drift_detected: bool,
        severity: str,
        reason: str,
        context_hash: Optional[str],
        result_hash: Optional[str],
        details: Optional[Dict[str, Any]] = None,
    ):
        self.drift_detected = drift_detected
        self.severity = severity
        self.reason = reason
        self.context_hash = context_hash
        self.result_hash = result_hash
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_detected": self.drift_detected,
            "severity": self.severity,
            "reason": self.reason,
            "context_hash": self.context_hash,
            "result_hash": self.result_hash,
            "details": self.details,
            "timestamp": self.timestamp,
        }


# -----------------------------------------------------------------
# DRIFT ENGINE
# -----------------------------------------------------------------

class DriftDetectionEngine:

    def __init__(self, event_bus: Optional[Any] = None):
        """
        :param event_bus: optional telemetry / event streaming
        """
        self.event_bus = event_bus

    # -----------------------------------------------------------------
    # MAIN ENTRYPOINT
    # -----------------------------------------------------------------

    def detect(
        self,
        context: RuntimeContext,
        original: ExecutionResult,
        replay: Optional[ExecutionResult] = None
    ) -> DriftReport:
        """
        Detect drift between original and replayed executions
        """

        if not isinstance(original, ExecutionResult):
            raise DriftDetectionError("Invalid original result")

        if context and not context.verify():
            return self._report(
                True, "HIGH", "CONTEXT_TAMPERING",
                context, original
            )

        # ---------------------------------------------------------
        # Case 1: Replay available
        # ---------------------------------------------------------
        if replay:

            if original.result_hash != replay.result_hash:
                severity = self._classify_severity(original, replay)

                return self._report(
                    True,
                    severity,
                    "REPLAY_DIVERGENCE",
                    context,
                    original,
                    {
                        "original_output": original.output,
                        "replay_output": replay.output
                    }
                )

        # ---------------------------------------------------------
        # Case 2: Validate structural integrity
        # ---------------------------------------------------------
        if not self._is_output_valid(original.output):
            return self._report(
                True,
                "HIGH",
                "INVALID_OUTPUT_STRUCTURE",
                context,
                original
            )

        # ---------------------------------------------------------
        # Case 3: Success
        # ---------------------------------------------------------
        self._emit({
            "type": "DRIFT_CHECK_PASSED",
            "context_hash": context.context_hash if context else None
        })

        return self._report(
            False,
            "NONE",
            "NO_DRIFT",
            context,
            original
        )

    # -----------------------------------------------------------------
    # OUTPUT VALIDATION
    # -----------------------------------------------------------------

    def _is_output_valid(self, output: Optional[Dict[str, Any]]) -> bool:
        """
        Detect structural issues in execution output
        """

        if output is None:
            return False

        try:
            json.dumps(output, sort_keys=True)
            return True
        except Exception:
            return False

    # -----------------------------------------------------------------
    # SEVERITY CLASSIFICATION
    # -----------------------------------------------------------------

    def _classify_severity(
        self,
        original: ExecutionResult,
        replay: ExecutionResult
    ) -> str:
        """
        Basic severity classification
        """

        if not replay.success:
            return "CRITICAL"

        if original.success and not replay.success:
            return "HIGH"

        if original.output != replay.output:
            return "MEDIUM"

        return "LOW"

    # -----------------------------------------------------------------
    # REPORT BUILDER
    # -----------------------------------------------------------------

    def _report(
        self,
        drift: bool,
        severity: str,
        reason: str,
        context: Optional[RuntimeContext],
        result: ExecutionResult,
        details: Optional[Dict[str, Any]] = None
    ) -> DriftReport:

        report = DriftReport(
            drift_detected=drift,
            severity=severity,
            reason=reason,
            context_hash=context.context_hash if context else None,
            result_hash=result.result_hash,
            details=details
        )

        self._emit({
            "type": "DRIFT_REPORT",
            "drift": drift,
            "severity": severity,
            "reason": reason
        })

        if drift:
            raise DriftDetectionError(reason, report)

        return report

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
