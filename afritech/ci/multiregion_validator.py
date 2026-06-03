"""Validate multi-region convergence proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.runtime.multiregion.proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    MultiRegionProofError,
    MultiRegionProofReport,
    run_multiregion_proof,
)


class MultiRegionValidationError(RuntimeError):
    """Raised when multi-region convergence validation fails."""


@dataclass(frozen=True)
class MultiRegionValidationReport:
    scenarios: tuple[str, ...]
    multiregion_convergence_hash: str

    @property
    def verified(self) -> bool:
        return (
            self.scenarios == REQUIRED_SCENARIOS
            and len(self.multiregion_convergence_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "multiregion_convergence_hash": self.multiregion_convergence_hash,
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.multiregion_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> MultiRegionValidationReport:
    try:
        proof = run_multiregion_proof()
    except MultiRegionProofError as exc:
        raise MultiRegionValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = MultiRegionValidationReport(
        multiregion_convergence_hash=proof.multiregion_convergence_hash,
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise MultiRegionValidationError("multi-region validation report failed")
    return report


def _validate_proof(proof: MultiRegionProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise MultiRegionValidationError("multi-region scenario set mismatch")
    for scenario in proof.scenarios:
        consistency = scenario.consistency
        if not scenario.verified:
            raise MultiRegionValidationError(
                f"multi-region scenario failed: {scenario.scenario}"
            )
        if not consistency.truth_unique:
            raise MultiRegionValidationError("region-relative truth detected")
        if not consistency.identity_consistent:
            raise MultiRegionValidationError("identity drift across regions")
        if not consistency.admissibility_consistent:
            raise MultiRegionValidationError("admissibility drift across regions")
        if not consistency.convergence_consistent:
            raise MultiRegionValidationError("convergence drift across regions")


def _validate_report_files(
    proof: MultiRegionProofReport,
    report_dir: Path = Path("reports/multiregion_proof_v1"),
) -> None:
    equivalence_path = report_dir / "multiregion_equivalence.json"
    if not equivalence_path.exists():
        raise MultiRegionValidationError("missing multi-region equivalence report")
    equivalence = _load_json(equivalence_path)
    if (
        equivalence.get("multiregion_convergence_hash")
        != proof.multiregion_convergence_hash
    ):
        raise MultiRegionValidationError("multi-region convergence hash mismatch")
    if equivalence.get("equivalent") is not True:
        raise MultiRegionValidationError(
            "multi-region equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise MultiRegionValidationError(
                f"missing multi-region scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise MultiRegionValidationError(
                f"multi-region scenario mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise MultiRegionValidationError(
                f"multi-region scenario not verified: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MultiRegionValidationError(f"report must be object: {path}")
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
    except MultiRegionValidationError as exc:
        print(f"Multi-region validation FAILED: {exc}")
        return 1

    print(
        "Multi-region validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"multiregion_convergence_hash={report.multiregion_convergence_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

