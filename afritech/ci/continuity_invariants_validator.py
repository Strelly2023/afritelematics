"""Validate continuity proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.continuity.engine.proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    ContinuityProofError,
    ContinuityProofReport,
    run_continuity_proof,
)


class ContinuityInvariantsValidationError(RuntimeError):
    """Raised when continuity invariant validation fails."""


@dataclass(frozen=True)
class ContinuityInvariantsValidationReport:
    scenarios: tuple[str, ...]
    continuity_equivalence_hash: str

    @property
    def verified(self) -> bool:
        return (
            self.scenarios == REQUIRED_SCENARIOS
            and len(self.continuity_equivalence_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "continuity_equivalence_hash": self.continuity_equivalence_hash,
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.continuity_invariants_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> ContinuityInvariantsValidationReport:
    try:
        proof = run_continuity_proof()
    except ContinuityProofError as exc:
        raise ContinuityInvariantsValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = ContinuityInvariantsValidationReport(
        continuity_equivalence_hash=proof.continuity_equivalence_hash,
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise ContinuityInvariantsValidationError("continuity invariant report failed")
    return report


def _validate_proof(proof: ContinuityProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise ContinuityInvariantsValidationError("continuity scenario set mismatch")
    for scenario in proof.scenarios:
        if not scenario.no_invented_truth:
            raise ContinuityInvariantsValidationError(
                f"invented truth detected: {scenario.scenario}"
            )
        if scenario.result.complete and not scenario.equivalent_when_complete:
            raise ContinuityInvariantsValidationError(
                f"continuity replay hash drift: {scenario.scenario}"
            )
        if scenario.result.status == "deferrable" and not scenario.result.gaps:
            raise ContinuityInvariantsValidationError(
                f"deferrable scenario missing gap evidence: {scenario.scenario}"
            )


def _validate_report_files(
    proof: ContinuityProofReport,
    report_dir: Path = Path("reports/continuity_proof_v1"),
) -> None:
    equivalence_path = report_dir / "continuity_equivalence.json"
    if not equivalence_path.exists():
        raise ContinuityInvariantsValidationError(
            "missing continuity equivalence report"
        )
    equivalence = _load_json(equivalence_path)
    if (
        equivalence.get("continuity_equivalence_hash")
        != proof.continuity_equivalence_hash
    ):
        raise ContinuityInvariantsValidationError(
            "continuity equivalence hash mismatch"
        )
    if equivalence.get("equivalent") is not True:
        raise ContinuityInvariantsValidationError(
            "continuity equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise ContinuityInvariantsValidationError(
                f"missing continuity scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise ContinuityInvariantsValidationError(
                f"continuity scenario report name mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise ContinuityInvariantsValidationError(
                f"continuity scenario report not verified: {filename}"
            )
        if payload.get("no_invented_truth") is not True:
            raise ContinuityInvariantsValidationError(
                f"continuity scenario invented truth: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContinuityInvariantsValidationError(f"report must be object: {path}")
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
    except ContinuityInvariantsValidationError as exc:
        print(f"Continuity validation FAILED: {exc}")
        return 1

    print(
        "Continuity validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"continuity_equivalence_hash={report.continuity_equivalence_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

