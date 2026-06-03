"""Multi-region convergence proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.runtime.multiregion.consistency_validator import (
    MultiRegionConsistency,
    validate_consistency,
)
from afritech.runtime.multiregion.convergence_engine import GlobalConvergenceResult, converge_regions
from afritech.runtime.multiregion.partition_simulator import partition_regions
from afritech.runtime.multiregion.region_model import execute_regions


AUTHORITY_LAW = "Region-local disruption must not create region-relative truth."

REQUIRED_SCENARIOS = (
    "full_partition",
    "conflicting_local_order",
    "delayed_cross_region_sync",
    "independent_recovery",
    "duplicate_cross_region_messages",
)

REPORT_FILES = {
    "full_partition": "partition_scenario.json",
    "conflicting_local_order": "cross_region_order.json",
    "delayed_cross_region_sync": "delayed_sync.json",
    "independent_recovery": "recovery_merge.json",
    "duplicate_cross_region_messages": "duplicate_cross_region_messages.json",
}


class MultiRegionProofError(RuntimeError):
    """Raised when multi-region proof detects region-relative truth."""


@dataclass(frozen=True)
class MultiRegionScenarioProof:
    scenario: str
    baseline_trace: tuple[Mapping[str, Any], ...]
    result: GlobalConvergenceResult
    consistency: MultiRegionConsistency

    @property
    def verified(self) -> bool:
        return self.result.equivalent and self.consistency.verified

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "baseline_trace": [_canonicalize(event) for event in self.baseline_trace],
            "consistency": self.consistency.canonical_dict(),
            "global_convergence": self.result.canonical_dict(),
            "scenario": self.scenario,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class MultiRegionProofReport:
    scenarios: tuple[MultiRegionScenarioProof, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
        )

    @property
    def multiregion_convergence_hash(self) -> str:
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
            "multiregion_convergence_hash": self.multiregion_convergence_hash,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afritech.multiregion_convergence_proof_report.v1",
            "verified": self.verified,
        }


def run_multiregion_proof() -> MultiRegionProofReport:
    report = MultiRegionProofReport(
        scenarios=tuple(_build_scenario(name) for name in REQUIRED_SCENARIOS)
    )
    if not report.verified:
        raise MultiRegionProofError("multi-region convergence proof failed")
    return report


def write_multiregion_proof_reports(
    output_dir: str | Path = "reports/multiregion_proof_v1",
) -> MultiRegionProofReport:
    report = run_multiregion_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "multiregion_equivalence.json",
        {
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "multiregion_convergence_hash": report.multiregion_convergence_hash,
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
            "schema": "afritech.multiregion_equivalence_report.v1",
        },
    )
    return report


def _build_scenario(name: str) -> MultiRegionScenarioProof:
    baseline = _baseline_trace()
    simulator_name = {
        "full_partition": "full_partition",
        "conflicting_local_order": "conflicting_local_order",
        "delayed_cross_region_sync": "delayed_sync",
        "independent_recovery": "independent_recovery",
        "duplicate_cross_region_messages": "duplicate_cross_region",
    }[name]
    views = partition_regions(simulator_name, baseline)
    regions = execute_regions(views, expected_sequence_end=len(baseline) - 1)
    result = converge_regions(baseline, regions)
    consistency = validate_consistency(result)
    return MultiRegionScenarioProof(
        baseline_trace=baseline,
        consistency=consistency,
        result=result,
        scenario=name,
    )


def _baseline_trace() -> tuple[Mapping[str, Any], ...]:
    return tuple(_event(index) for index in range(7))


def _event(index: int) -> dict[str, Any]:
    identity = "rider.multiregion.001" if index < 3 else "driver.multiregion.001"
    actions = (
        "request",
        "match",
        "price_quote",
        "accept",
        "pickup",
        "dropoff",
        "complete",
    )
    payload: dict[str, object] = {
        "action": actions[index],
        "ride_id": "ride.multiregion.001",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.multiregion.001"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1700
    return {
        "event_id": f"multiregion.event.{index:03d}",
        "identity_id": identity,
        "partition_id": _canonical_partition(identity),
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:02:{index:02d}Z",
    }


def _canonical_partition(identity_id: str) -> str:
    return f"partition.{sum(identity_id.encode('utf-8')) % 4}"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
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
        report = write_multiregion_proof_reports()
    except MultiRegionProofError as exc:
        print(f"Multi-region convergence proof FAILED: {exc}")
        return 1
    print(
        "Multi-region convergence proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"multiregion_convergence_hash={report.multiregion_convergence_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

