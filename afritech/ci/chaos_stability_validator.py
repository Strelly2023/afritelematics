"""Validate chaos repetition stability invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.simulation.chaos_v2.stability_proof import (
    REPORT_FILES,
    REQUIRED_CYCLE_COUNTS,
    ChaosStabilityProofError,
    ChaosStabilityProofReport,
    run_chaos_stability_proof,
)


class ChaosStabilityValidationError(RuntimeError):
    """Raised when chaos stability validation fails."""


@dataclass(frozen=True)
class ChaosStabilityValidationReport:
    cycle_counts: tuple[int, ...]
    chaos_stability_hash: str

    @property
    def verified(self) -> bool:
        return (
            self.cycle_counts == REQUIRED_CYCLE_COUNTS
            and len(self.chaos_stability_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chaos_stability_hash": self.chaos_stability_hash,
            "cycle_counts": list(self.cycle_counts),
            "schema": "afritech.chaos_stability_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> ChaosStabilityValidationReport:
    try:
        proof = run_chaos_stability_proof()
    except ChaosStabilityProofError as exc:
        raise ChaosStabilityValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = ChaosStabilityValidationReport(
        chaos_stability_hash=proof.chaos_stability_hash,
        cycle_counts=tuple(run.cycle_count for run in proof.runs),
    )
    if not report.verified:
        raise ChaosStabilityValidationError("chaos stability report failed")
    return report


def _validate_proof(proof: ChaosStabilityProofReport) -> None:
    if tuple(run.cycle_count for run in proof.runs) != REQUIRED_CYCLE_COUNTS:
        raise ChaosStabilityValidationError("chaos cycle count set mismatch")
    for run in proof.runs:
        if not run.verified:
            raise ChaosStabilityValidationError(
                f"chaos run failed: cycle_count={run.cycle_count}"
            )
        for cycle in run.cycles:
            if cycle.drift.drift_detected:
                raise ChaosStabilityValidationError(
                    f"chaos drift detected at cycle {cycle.cycle}"
                )
            if not cycle.final_result.complete:
                raise ChaosStabilityValidationError(
                    f"chaos recovery incomplete at cycle {cycle.cycle}"
                )
            if (
                cycle.final_result.convergence.identity_resolution_hash
                != run.baseline_hashes["identity_resolution_hash"]
            ):
                raise ChaosStabilityValidationError(
                    f"identity mutation at cycle {cycle.cycle}"
                )


def _validate_report_files(
    proof: ChaosStabilityProofReport,
    report_dir: Path = Path("reports/chaos_proof_v1"),
) -> None:
    equivalence_path = report_dir / "stability_equivalence.json"
    if not equivalence_path.exists():
        raise ChaosStabilityValidationError("missing chaos stability equivalence report")
    equivalence = _load_json(equivalence_path)
    if equivalence.get("chaos_stability_hash") != proof.chaos_stability_hash:
        raise ChaosStabilityValidationError("chaos stability hash mismatch")
    if equivalence.get("equivalent") is not True:
        raise ChaosStabilityValidationError(
            "chaos stability equivalence report is not equivalent"
        )

    drift_path = report_dir / "drift_analysis.json"
    if not drift_path.exists():
        raise ChaosStabilityValidationError("missing chaos drift analysis report")
    drift = _load_json(drift_path)
    if drift.get("drift_detected") is not False or drift.get("verified") is not True:
        raise ChaosStabilityValidationError("chaos drift analysis reports drift")

    runs = {run.cycle_count: run for run in proof.runs}
    for cycle_count, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise ChaosStabilityValidationError(
                f"missing chaos run report: {filename}"
            )
        payload = _load_json(path)
        run = runs[cycle_count]
        if payload.get("cycle_count") != run.cycle_count:
            raise ChaosStabilityValidationError(
                f"chaos run report cycle mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise ChaosStabilityValidationError(
                f"chaos run report not verified: {filename}"
            )
        if payload.get("run_hash") != run.run_hash:
            raise ChaosStabilityValidationError(
                f"chaos run hash mismatch: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ChaosStabilityValidationError(f"report must be object: {path}")
    return payload


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
        report = validate()
    except ChaosStabilityValidationError as exc:
        print(f"Chaos stability validation FAILED: {exc}")
        return 1

    print(
        "Chaos stability validation PASSED: "
        f"cycle_counts={list(report.cycle_counts)} "
        f"chaos_stability_hash={report.chaos_stability_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

