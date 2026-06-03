"""Entropy-bound execution proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.convergence import ConvergenceResult, converge


AUTHORITY_LAW = "Failure may enter execution. Failure may not define truth."

REQUIRED_SCENARIOS = (
    "network_partition",
    "duplicate_messages",
    "out_of_order_events",
    "clock_drift",
    "partial_corruption",
    "offline_recovery",
)

REPORT_FILES = {
    "network_partition": "partition_test.json",
    "duplicate_messages": "duplicate_test.json",
    "out_of_order_events": "delay_test.json",
    "clock_drift": "clock_drift_test.json",
    "partial_corruption": "corruption_test.json",
    "offline_recovery": "offline_recovery_test.json",
}


class EntropyProofError(RuntimeError):
    """Raised when entropy-bound execution proof detects divergence."""


@dataclass(frozen=True)
class EntropyScenarioProof:
    scenario: str
    input_variations: tuple[tuple[Mapping[str, Any], ...], ...]
    baseline: ConvergenceResult
    disturbed: ConvergenceResult

    @property
    def same_replay_hash(self) -> bool:
        return self.baseline.replay_hash == self.disturbed.replay_hash

    @property
    def same_identity_resolution(self) -> bool:
        return (
            self.baseline.identity_resolution_hash
            == self.disturbed.identity_resolution_hash
        )

    @property
    def same_admissibility_decision(self) -> bool:
        return self.baseline.admissibility_hash == self.disturbed.admissibility_hash

    @property
    def same_convergence_result(self) -> bool:
        return self.baseline.convergence_hash == self.disturbed.convergence_hash

    @property
    def equivalent(self) -> bool:
        return (
            self.same_replay_hash
            and self.same_identity_resolution
            and self.same_admissibility_decision
            and self.same_convergence_result
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "baseline": self.baseline.canonical_dict(),
            "disturbed": self.disturbed.canonical_dict(),
            "equivalent": self.equivalent,
            "final_state": self.disturbed.final_state,
            "input_variations": [
                [_canonicalize(event) for event in variation]
                for variation in self.input_variations
            ],
            "invariants": {
                "same_admissibility_decision": self.same_admissibility_decision,
                "same_convergence_result": self.same_convergence_result,
                "same_identity_resolution": self.same_identity_resolution,
                "same_replay_hash": self.same_replay_hash,
            },
            "normalized_inputs": [
                record.event.canonical_dict() for record in self.disturbed.records
            ],
            "replay_hash": self.disturbed.replay_hash,
            "scenario": self.scenario,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class EntropyProofReport:
    scenarios: tuple[EntropyScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.equivalent for scenario in self.scenarios)
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "schema": "afritech.entropy_bound_execution_proof_report.v1",
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_entropy_bound_execution_proof() -> EntropyProofReport:
    scenarios = tuple(_build_scenario(name) for name in REQUIRED_SCENARIOS)
    report = EntropyProofReport(scenarios=scenarios)
    if not report.verified:
        raise EntropyProofError("entropy-bound execution proof failed")
    return report


def write_entropy_proof_reports(
    output_dir: str | Path = "reports/entropy_proof_v1",
) -> EntropyProofReport:
    report = run_entropy_bound_execution_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        filename = REPORT_FILES[scenario.scenario]
        _write_json(target / filename, scenario.canonical_dict())
    _write_json(
        target / "replay_equivalence_report.json",
        {
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "report_hash": report.report_hash(),
            "replay_hashes": {
                scenario.scenario: scenario.disturbed.replay_hash
                for scenario in report.scenarios
            },
            "schema": "afritech.entropy_replay_equivalence_report.v1",
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
        },
    )
    return report


def _build_scenario(name: str) -> EntropyScenarioProof:
    baseline_events = _baseline_events()
    disturbed_events = _disturbed_events(name)
    baseline = converge(baseline_events)
    disturbed = converge(disturbed_events)
    return EntropyScenarioProof(
        baseline=baseline,
        disturbed=disturbed,
        input_variations=(baseline_events, disturbed_events),
        scenario=name,
    )


def _baseline_events() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(6))


def _disturbed_events(name: str) -> tuple[Mapping[str, Any], ...]:
    baseline = list(_baseline_events())
    if name == "network_partition":
        return tuple(
            _with(event, received_order=event["sequence"] + 5, partition_id="partition.split")
            if event["sequence"] in (1, 2)
            else event
            for event in baseline
        )
    if name == "duplicate_messages":
        return tuple((*baseline[:3], baseline[1], *baseline[3:]))
    if name == "out_of_order_events":
        return tuple((baseline[3], baseline[0], baseline[2], baseline[1], *baseline[4:]))
    if name == "clock_drift":
        return tuple(
            _with(event, source_timestamp=f"drift:node-clock:{999 - event['sequence']}")
            for event in baseline
        )
    if name == "partial_corruption":
        corrupted_duplicate = _with(
            baseline[2],
            corrupted=True,
            payload="malformed-provider-fragment",
        )
        return tuple((*baseline[:3], corrupted_duplicate, *baseline[3:]))
    if name == "offline_recovery":
        return tuple(
            _with(event, source="offline_recovery", received_order=event["sequence"] + 20)
            for event in reversed(baseline)
        )
    raise EntropyProofError(f"unknown entropy scenario: {name}")


def _event(index: int) -> dict[str, Any]:
    identity = "rider.entropy.001" if index < 3 else "driver.entropy.001"
    return {
        "event_id": f"entropy.event.{index:03d}",
        "identity_id": identity,
        "partition_id": _canonical_partition(identity),
        "payload": {
            "action": (
                "request"
                if index == 0
                else "match"
                if index == 1
                else "accept"
                if index == 2
                else "pickup"
                if index == 3
                else "dropoff"
                if index == 4
                else "complete"
            ),
            "ride_id": "ride.entropy.001",
        },
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-26T00:00:{index:02d}Z",
    }


def _with(event: Mapping[str, Any], **updates: Any) -> dict[str, Any]:
    clone = dict(event)
    clone.update(updates)
    return clone


def _canonical_partition(identity_id: str) -> str:
    return f"partition.{sum(identity_id.encode('utf-8')) % 4}"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
