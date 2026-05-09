"""
afritech/evaluation/adr_trigger/adr_trigger_engine.py

ADR Trigger Engine
=================

Detects execution conditions that require governance decisions.

Responsibilities:
- Monitor execution outputs
- Identify drift / anomalies
- Trigger ADR creation when required
"""

from typing import Dict, Any, Optional


class ADRTriggerError(Exception):
    pass


class ADRTriggerEngine:

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        """
        :param rules: configurable trigger rules
        """
        self.rules = rules or {
            "drift_required": True,
            "error_threshold": True,
        }

    # -----------------------------------------------------------------
    # PRIMARY EVALUATION
    # -----------------------------------------------------------------

    def evaluate(self, context: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns:
        {
            "trigger": bool,
            "reason": str
        }
        """

        if not isinstance(result, dict):
            raise ADRTriggerError("Result must be dictionary")

        # ---------------------------------------------------------
        # RULE 1: Drift detection
        # ---------------------------------------------------------
        if self.rules.get("drift_required") and result.get("drift_detected"):
            return {
                "trigger": True,
                "reason": "DRIFT_DETECTED"
            }

        # ---------------------------------------------------------
        # RULE 2: Execution failure
        # ---------------------------------------------------------
        if self.rules.get("error_threshold") and result.get("success") is False:
            return {
                "trigger": True,
                "reason": "EXECUTION_FAILURE"
            }

        return {
            "trigger": False,
            "reason": "NO_ACTION"
        }

    # -----------------------------------------------------------------
    # SYNTHETIC TRIGGER (MANUAL / FORCED)
    # -----------------------------------------------------------------

    def force_trigger(self, reason: str) -> Dict[str, Any]:
        return {
            "trigger": True,
            "reason": reason
        }
