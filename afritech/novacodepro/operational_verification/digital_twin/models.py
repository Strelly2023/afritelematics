from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelemetryProfile:
    sample_size: int
    fresh: bool
    device_coverage: bool
    network_coverage: bool
    journey_coverage: bool
    accessibility_coverage: bool
    region_coverage: bool
    static_seed_only: bool = False


@dataclass(frozen=True, slots=True)
class SimulationResult:
    scenario: str
    executed: bool
    verified: bool
    journey_completion_prediction: str
    operational_risk: str
    confidence_interval: str
    forbidden_side_effects: bool = False
