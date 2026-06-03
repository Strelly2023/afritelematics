"""Continuity proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.continuity.engine.reconstruct import (
    ReconstructionResult,
    reconstruct_trace,
)
from afritech.runtime.entropy.convergence import converge


AUTHORITY_LAW = "Missing information must never result in invented truth."

REQUIRED_SCENARIOS = (
    "partial_trace_recovery",
    "offline_node_merge",
    "missing_segment_replay",
    "delayed_completion",
    "corrupted_segment_isolation",
)

REPORT_FILES = {
    "partial_trace_recovery": "partial_replay.json",
    "offline_node_merge": "offline_merge.json",
    "missing_segment_replay": "gap_detection.json",
    "delayed_completion": "recovery_equivalence.json",
    "corrupted_segment_isolation": "corrupted_segment_isolation.json",
}


class ContinuityProofError(RuntimeError):
    """Raised when continuity proof detects invented or divergent truth."""


@dataclass(frozen=True)
class ContinuityScenarioProof:
    scenario: str
    full_trace: tuple[Mapping[str, Any], ...]
    partial_trace: tuple[Mapping[str, Any], ...]
    recovery_trace: tuple[Mapping[str, Any], ...]
    result: ReconstructionResult

    @property
    def full_replay_hash(self) -> str:
        return converge(self.full_trace).replay_hash

    @property
    def reconstructed_replay_hash(self) -> str:
        return self.result.convergence.replay_hash

    @property
    def equivalent_when_complete(self) -> bool:
        if not self.result.complete:
            return True
        return self.full_replay_hash == self.reconstructed_replay_hash

    @property
    def no_invented_truth(self) -> bool:
        provided_sequences = {
            int(event["sequence"]) for event in (*self.partial_trace, *self.recovery_trace)
        }
        accepted_sequences = {event.sequence for event in self.result.accepted_events}
        return accepted_sequences <= provided_sequences

    @property
    def verified(self) -> bool:
        return self.equivalent_when_complete and self.no_invented_truth

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "equivalent_when_complete": self.equivalent_when_complete,
            "full_replay_hash": self.full_replay_hash,
            "full_trace": [_canonicalize(event) for event in self.full_trace],
            "input_variations": {
                "partial_trace": [_canonicalize(event) for event in self.partial_trace],
                "recovery_trace": [_canonicalize(event) for event in self.recovery_trace],
            },
            "no_invented_truth": self.no_invented_truth,
            "reconstructed_replay_hash": self.reconstructed_replay_hash,
            "reconstruction": self.result.canonical_dict(),
            "scenario": self.scenario,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class ContinuityProofReport:
    scenarios: tuple[ContinuityScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
        )

    @property
    def continuity_equivalence_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_law": AUTHORITY_LAW,
                "scenario_hashes": {
                    scenario.scenario: scenario.report_hash()
                    for scenario in self.scenarios
                },
                "verified": self.verified,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "continuity_equivalence_hash": self.continuity_equivalence_hash,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "schema": "afritech.continuity_proof_report.v1",
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "verified": self.verified,
        }


def run_continuity_proof() -> ContinuityProofReport:
    report = ContinuityProofReport(
        scenarios=tuple(_build_scenario(name) for name in REQUIRED_SCENARIOS)
    )
    if not report.verified:
        raise ContinuityProofError("continuity proof failed")
    return report


def write_continuity_proof_reports(
    output_dir: str | Path = "reports/continuity_proof_v1",
) -> ContinuityProofReport:
    report = run_continuity_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "continuity_equivalence.json",
        {
            "authority_law": AUTHORITY_LAW,
            "continuity_equivalence_hash": report.continuity_equivalence_hash,
            "equivalent": report.verified,
            "replay_hashes": {
                scenario.scenario: scenario.reconstructed_replay_hash
                for scenario in report.scenarios
            },
            "schema": "afritech.continuity_equivalence_report.v1",
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
        },
    )
    return report


def _build_scenario(name: str) -> ContinuityScenarioProof:
    full = _baseline_events()
    if name == "partial_trace_recovery":
        partial = (full[0], full[1], full[3], full[4])
        recovery: tuple[Mapping[str, Any], ...] = ()
    elif name == "offline_node_merge":
        partial = (full[0], full[1], full[3], full[4], full[5])
        recovery = full
    elif name == "missing_segment_replay":
        partial = (full[0], full[1], full[4], full[5])
        recovery = ()
    elif name == "delayed_completion":
        partial = (full[0], full[1], full[3], full[4], full[5])
        recovery = (full[2],)
    elif name == "corrupted_segment_isolation":
        corrupted = _with(
            full[2],
            corrupted=True,
            payload={"admissibility_truth": "forged", "ride_id": "ride.continuity.001"},
        )
        partial = (full[0], full[1], corrupted, full[3], full[4], full[5])
        recovery = ()
    else:
        raise ContinuityProofError(f"unknown continuity scenario: {name}")

    result = reconstruct_trace(
        partial,
        recovery_trace=recovery,
        expected_sequence_end=len(full) - 1,
    )
    return ContinuityScenarioProof(
        full_trace=full,
        partial_trace=partial,
        recovery_trace=recovery,
        result=result,
        scenario=name,
    )


def _baseline_events() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(6))


def _event(index: int) -> dict[str, Any]:
    identity = "rider.continuity.001" if index < 3 else "driver.continuity.001"
    actions = ("request", "match", "accept", "pickup", "dropoff", "complete")
    return {
        "event_id": f"continuity.event.{index:03d}",
        "identity_id": identity,
        "partition_id": _canonical_partition(identity),
        "payload": {
            "action": actions[index],
            "ride_id": "ride.continuity.001",
        },
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:00:{index:02d}Z",
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


def main() -> int:
    try:
        report = write_continuity_proof_reports()
    except ContinuityProofError as exc:
        print(f"Continuity proof FAILED: {exc}")
        return 1
    print(
        "Continuity proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"continuity_equivalence_hash={report.continuity_equivalence_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
