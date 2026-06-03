"""Validate AfriRide field proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.field_proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    AfriRideFieldProofError,
    AfriRideFieldProofReport,
    run_afriride_field_proof,
)


class AfriRideFieldValidationError(RuntimeError):
    """Raised when AfriRide field validation fails."""


@dataclass(frozen=True)
class AfriRideFieldValidationReport:
    scenarios: tuple[str, ...]
    afriride_field_hash: str

    @property
    def verified(self) -> bool:
        return self.scenarios == REQUIRED_SCENARIOS and len(self.afriride_field_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "afriride_field_hash": self.afriride_field_hash,
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afriride.field_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRideFieldValidationReport:
    try:
        proof = run_afriride_field_proof()
    except AfriRideFieldProofError as exc:
        raise AfriRideFieldValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = AfriRideFieldValidationReport(
        afriride_field_hash=proof.afriride_field_hash,
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise AfriRideFieldValidationError("AfriRide field validation report failed")
    return report


def _validate_proof(proof: AfriRideFieldProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise AfriRideFieldValidationError("AfriRide field scenario set mismatch")
    for scenario in proof.scenarios:
        replay = scenario.replay
        if not replay.replay_match:
            raise AfriRideFieldValidationError(f"replay mismatch: {scenario.scenario}")
        if not replay.identity_match:
            raise AfriRideFieldValidationError(f"identity mismatch: {scenario.scenario}")
        if not replay.pricing_match:
            raise AfriRideFieldValidationError(f"pricing deviation: {scenario.scenario}")
        if not replay.admissibility_match:
            raise AfriRideFieldValidationError(
                f"admissibility divergence: {scenario.scenario}"
            )
        if not scenario.dispute_match:
            raise AfriRideFieldValidationError(f"dispute mismatch: {scenario.scenario}")


def _validate_report_files(
    proof: AfriRideFieldProofReport,
    report_dir: Path = Path("reports/afriride_field_proof_v1"),
) -> None:
    equivalence_path = report_dir / "field_equivalence.json"
    if not equivalence_path.exists():
        raise AfriRideFieldValidationError("missing AfriRide field equivalence report")
    equivalence = _load_json(equivalence_path)
    if equivalence.get("afriride_field_hash") != proof.afriride_field_hash:
        raise AfriRideFieldValidationError("AfriRide field hash mismatch")
    if equivalence.get("equivalent") is not True:
        raise AfriRideFieldValidationError(
            "AfriRide field equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise AfriRideFieldValidationError(
                f"missing AfriRide field scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise AfriRideFieldValidationError(
                f"AfriRide field scenario mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise AfriRideFieldValidationError(
                f"AfriRide field scenario not verified: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AfriRideFieldValidationError(f"report must be object: {path}")
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
    except AfriRideFieldValidationError as exc:
        print(f"AfriRide field validation FAILED: {exc}")
        return 1

    print(
        "AfriRide field validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"afriride_field_hash={report.afriride_field_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

