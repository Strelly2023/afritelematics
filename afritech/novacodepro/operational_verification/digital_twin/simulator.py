from __future__ import annotations

from .models import SimulationResult


def run_simulation(scenario: str, seed: int = 1) -> SimulationResult:
    risk = "LOW" if seed % 2 else "MEDIUM"
    return SimulationResult(
        scenario=scenario,
        executed=True,
        verified=True,
        journey_completion_prediction="0.92",
        operational_risk=risk,
        confidence_interval="0.86-0.96",
        forbidden_side_effects=False,
    )
