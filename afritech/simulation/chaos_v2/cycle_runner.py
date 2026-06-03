"""Run one repeated chaos cycle."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.continuity.engine.reconstruct import ReconstructionResult, reconstruct_trace
from afritech.runtime.entropy.convergence import converge
from afritech.simulation.chaos_v2.drift_analyzer import DriftAnalysis, detect_drift
from afritech.simulation.chaos_v2.scenario_generator import (
    ChaosScenario,
    apply_disturbance,
    apply_incompleteness,
    recovery_trace,
)


@dataclass(frozen=True)
class ChaosCycleResult:
    cycle: int
    scenario: ChaosScenario
    partial_result: ReconstructionResult
    final_result: ReconstructionResult
    drift: DriftAnalysis

    @property
    def verified(self) -> bool:
        return self.final_result.complete and not self.drift.drift_detected

    def canonical_dict(self) -> dict[str, object]:
        return {
            "cycle": self.cycle,
            "cycle_hash": self.cycle_hash,
            "drift": self.drift.canonical_dict(),
            "final_result": self.final_result.canonical_dict(),
            "partial_result": self.partial_result.canonical_dict(),
            "scenario": self.scenario.canonical_dict(),
            "verified": self.verified,
        }

    @property
    def cycle_hash(self) -> str:
        return _canonical_hash(
            {
                "cycle": self.cycle,
                "drift": self.drift.canonical_dict(),
                "scenario": self.scenario.canonical_dict(),
                "verified": self.verified,
            }
        )


def run_cycle(
    baseline_trace: tuple[Mapping[str, Any], ...],
    baseline_hashes: Mapping[str, str],
    scenario: ChaosScenario,
) -> ChaosCycleResult:
    disturbed = apply_disturbance(baseline_trace, scenario)
    incomplete = apply_incompleteness(disturbed, scenario)
    expected_end = len(baseline_trace) - 1
    partial_result = reconstruct_trace(
        incomplete,
        recovery_trace=recovery_trace(baseline_trace, scenario),
        expected_sequence_end=expected_end,
    )
    final_result = reconstruct_trace(
        incomplete,
        recovery_trace=baseline_trace,
        expected_sequence_end=expected_end,
    )
    drift = detect_drift(baseline_hashes, _hashes(final_result))
    return ChaosCycleResult(
        cycle=scenario.cycle,
        drift=drift,
        final_result=final_result,
        partial_result=partial_result,
        scenario=scenario,
    )


def baseline_hashes(trace: tuple[Mapping[str, Any], ...]) -> dict[str, str]:
    return _hashes_from_convergence(converge(trace))


def _hashes(result: ReconstructionResult) -> dict[str, str]:
    return _hashes_from_convergence(result.convergence)


def _hashes_from_convergence(result) -> dict[str, str]:
    return {
        "admissibility_hash": result.admissibility_hash,
        "convergence_hash": result.convergence_hash,
        "identity_resolution_hash": result.identity_resolution_hash,
        "replay_hash": result.replay_hash,
    }


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
