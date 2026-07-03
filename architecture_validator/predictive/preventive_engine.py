from __future__ import annotations

from typing import Any


class PreventiveEngine:
    def act(self, predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for prediction in predictions:
            action = str(prediction.get("preventive_action") or "WATCH")
            severity = str(prediction.get("severity") or "low")
            if action == "NONE":
                continue
            actions.append(
                {
                    "action": action,
                    "severity": severity,
                    "risk": str(prediction.get("risk") or "unknown"),
                    "scenario_id": str(prediction.get("scenario_id") or "unknown"),
                    "authority": "advisory_only",
                }
            )
        return actions
