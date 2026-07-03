from __future__ import annotations

from typing import Any

from architecture_validator.predictive.crisis import CrisisSimulator
from architecture_validator.predictive.economic_optimizer import EconomicOptimizer
from architecture_validator.predictive.multi_agent import MultiAgentCoordinator
from architecture_validator.predictive.predictive_engine import PredictiveEngine
from architecture_validator.predictive.refactor_engine import RefactorEngine


class AutonomousCycle:
    def run(self, twin_state: dict[str, Any]) -> dict[str, Any]:
        coordinator = MultiAgentCoordinator()
        risks = coordinator.run(twin_state)

        simulator = CrisisSimulator()
        crisis_results = simulator.run(twin_state)
        crisis_summary = {
            "max_risk_score": max((int(item.get("risk_score") or 0) for item in crisis_results), default=0),
            "critical_scenarios": [item for item in crisis_results if item.get("impact") == "CRITICAL"],
        }

        metrics = twin_state.get("metrics") if isinstance(twin_state.get("metrics"), dict) else {}
        optimizer = EconomicOptimizer()
        decision = optimizer.optimize(metrics)

        refactor = RefactorEngine()
        improvements = refactor.suggest(risks)

        predictor = PredictiveEngine()
        predictive = predictor.predict(twin_state)

        return {
            "risks": risks,
            "crisis": crisis_results,
            "crisis_summary": crisis_summary,
            "decision": decision,
            "improvements": improvements,
            "predictive": predictive,
            "authority_boundary": "advisory_only",
        }
