from __future__ import annotations

from typing import Any

from architecture_validator.predictive.preventive_engine import PreventiveEngine
from architecture_validator.predictive.simulation import SimulationEngine


class PredictiveEngine:
    def predict(self, twin_state: dict[str, Any]) -> dict[str, Any]:
        simulation = SimulationEngine()
        predictions = simulation.run(twin_state)
        prevention = PreventiveEngine()
        actions = prevention.act(predictions)
        predicted_risks = sum(1 for item in predictions if item.get("severity") in {"high", "critical"})
        prevented_violations = sum(
            1 for item in actions if item.get("action") in {"BLOCK_DEPLOYMENT", "REQUIRE_NOVAPOWER_APPROVAL", "ENABLE_REPLAY_GATE", "REQUIRE_POLICY_CHECK"}
        )
        twin_health_score = int(twin_state.get("twin_health_score") or 0)
        risk_score = max(0, min(100, 100 - twin_health_score + (predicted_risks * 8)))
        return {
            "predictions": predictions,
            "preventive_actions": actions,
            "predicted_risks": predicted_risks,
            "prevented_violations": prevented_violations,
            "risk_score": risk_score,
            "twin_health_score": twin_health_score,
        }
