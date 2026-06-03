"""Chaos repetition stability proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.simulation.chaos_v2.orchestrator import ChaosRunResult, run_chaos_cycles


AUTHORITY_LAW = "Repeated disorder must not accumulate drift in truth."

REQUIRED_CYCLE_COUNTS = (10, 100)

REPORT_FILES = {
    10: "cycle_10.json",
    100: "cycle_100.json",
}


class ChaosStabilityProofError(RuntimeError):
    """Raised when repeated chaos produces cumulative drift."""


@dataclass(frozen=True)
class ChaosStabilityProofReport:
    runs: tuple[ChaosRunResult, ...]

    @property
    def verified(self) -> bool:
        return (
            tuple(run.cycle_count for run in self.runs) == REQUIRED_CYCLE_COUNTS
            and all(run.verified for run in self.runs)
        )

    @property
    def chaos_stability_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_law": AUTHORITY_LAW,
                "run_hashes": {run.cycle_count: run.run_hash for run in self.runs},
                "verified": self.verified,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_law": AUTHORITY_LAW,
            "chaos_stability_hash": self.chaos_stability_hash,
            "required_cycle_counts": list(REQUIRED_CYCLE_COUNTS),
            "runs": [run.canonical_dict() for run in self.runs],
            "schema": "afritech.chaos_stability_proof_report.v1",
            "verified": self.verified,
        }


def run_chaos_stability_proof() -> ChaosStabilityProofReport:
    report = ChaosStabilityProofReport(
        runs=tuple(run_chaos_cycles(count) for count in REQUIRED_CYCLE_COUNTS)
    )
    if not report.verified:
        raise ChaosStabilityProofError("chaos stability proof failed")
    return report


def write_chaos_proof_reports(
    output_dir: str | Path = "reports/chaos_proof_v1",
) -> ChaosStabilityProofReport:
    report = run_chaos_stability_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for run in report.runs:
        _write_json(target / REPORT_FILES[run.cycle_count], run.canonical_dict())
    _write_json(target / "drift_analysis.json", _drift_analysis_report(report))
    _write_json(
        target / "stability_equivalence.json",
        {
            "authority_law": AUTHORITY_LAW,
            "chaos_stability_hash": report.chaos_stability_hash,
            "equivalent": report.verified,
            "run_hashes": {
                str(run.cycle_count): run.run_hash for run in report.runs
            },
            "schema": "afritech.chaos_stability_equivalence_report.v1",
        },
    )
    return report


def _drift_analysis_report(report: ChaosStabilityProofReport) -> dict[str, object]:
    drifted = [
        {
            "cycle": cycle.cycle,
            "cycle_count": run.cycle_count,
            "drift": cycle.drift.canonical_dict(),
        }
        for run in report.runs
        for cycle in run.cycles
        if cycle.drift.drift_detected
    ]
    return {
        "authority_law": AUTHORITY_LAW,
        "drift_detected": bool(drifted),
        "drifted_cycles": drifted,
        "schema": "afritech.chaos_drift_analysis_report.v1",
        "total_cycles": sum(run.cycle_count for run in report.runs),
        "verified": not drifted,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = write_chaos_proof_reports()
    except ChaosStabilityProofError as exc:
        print(f"Chaos stability proof FAILED: {exc}")
        return 1
    print(
        "Chaos stability proof PASSED: "
        f"cycle_counts={list(REQUIRED_CYCLE_COUNTS)} "
        f"chaos_stability_hash={report.chaos_stability_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

