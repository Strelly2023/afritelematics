from __future__ import annotations

from typing import Any


class CrisisSimulator:
    SCENARIOS = (
        "PAYMENT_FAILURE",
        "API_OVERLOAD",
        "AI_DRIFT",
        "REPLAY_MISMATCH",
        "DB_FAILURE",
        "BLACK_SWAN_PAYMENT_OUTAGE",
    )

    def run(self, twin_state: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        twin_health = int(twin_state.get("digital_twin", {}).get("twin_health_score") or 0)
        predicted_risks = int(twin_state.get("predicted_risks") or 0)
        for scenario in self.SCENARIOS:
            risk_score = self._score(scenario, twin_health, predicted_risks)
            results.append(
                {
                    "scenario": scenario,
                    "risk_score": risk_score,
                    "impact": "CRITICAL" if risk_score >= 85 else "HIGH" if risk_score >= 65 else "LOW",
                    "requires": "manual_intervention" if risk_score >= 85 else "governed_monitoring",
                    "authority_boundary": "simulation_only",
                }
            )
        return results

    def simulate_black_swan(self) -> dict[str, str]:
        return {
            "event": "GLOBAL_PAYMENT_FAILURE",
            "impact": "CRITICAL",
            "requires": "manual_intervention",
            "authority_boundary": "simulation_only",
        }

    def _score(self, scenario: str, twin_health: int, predicted_risks: int) -> int:
        base_scores = {
            "PAYMENT_FAILURE": 88,
            "API_OVERLOAD": 72,
            "AI_DRIFT": 67,
            "REPLAY_MISMATCH": 90,
            "DB_FAILURE": 83,
            "BLACK_SWAN_PAYMENT_OUTAGE": 98,
        }
        score = base_scores.get(scenario, 50)
        score += max(0, 20 - int(round(twin_health / 8)))
        score += min(10, predicted_risks * 2)
        return max(0, min(100, score))
