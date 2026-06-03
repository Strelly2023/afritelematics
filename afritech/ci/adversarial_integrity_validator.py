"""Validate Gate 7 adversarial integrity proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.security.adversarial_integrity_proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    AdversarialIntegrityProofError,
    AdversarialIntegrityProofReport,
    run_adversarial_integrity_proof,
)


class AdversarialIntegrityValidationError(RuntimeError):
    """Raised when adversarial integrity validation fails."""


@dataclass(frozen=True)
class AdversarialIntegrityValidationReport:
    scenarios: tuple[str, ...]
    adversarial_integrity_hash: str

    @property
    def verified(self) -> bool:
        return (
            self.scenarios == REQUIRED_SCENARIOS
            and len(self.adversarial_integrity_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adversarial_integrity_hash": self.adversarial_integrity_hash,
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.adversarial_integrity_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AdversarialIntegrityValidationReport:
    try:
        proof = run_adversarial_integrity_proof()
    except AdversarialIntegrityProofError as exc:
        raise AdversarialIntegrityValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = AdversarialIntegrityValidationReport(
        adversarial_integrity_hash=proof.adversarial_integrity_hash,
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise AdversarialIntegrityValidationError(
            "adversarial integrity validation report failed"
        )
    return report


def _validate_proof(proof: AdversarialIntegrityProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise AdversarialIntegrityValidationError(
            "adversarial integrity scenario set mismatch"
        )
    for scenario in proof.scenarios:
        if not scenario.all_attacks_rejected:
            raise AdversarialIntegrityValidationError(
                f"adversarial attack admitted: {scenario.scenario}"
            )
        if not scenario.replay_truth_preserved:
            raise AdversarialIntegrityValidationError(
                f"adversarial replay drift: {scenario.scenario}"
            )
        if not scenario.authority_isolated:
            raise AdversarialIntegrityValidationError(
                f"adversarial authority leakage: {scenario.scenario}"
            )


def _validate_report_files(
    proof: AdversarialIntegrityProofReport,
    report_dir: Path = Path("reports/adversarial_integrity_proof_v1"),
) -> None:
    equivalence_path = report_dir / "adversarial_integrity_equivalence.json"
    if not equivalence_path.exists():
        raise AdversarialIntegrityValidationError(
            "missing adversarial integrity equivalence report"
        )
    equivalence = _load_json(equivalence_path)
    if (
        equivalence.get("adversarial_integrity_hash")
        != proof.adversarial_integrity_hash
    ):
        raise AdversarialIntegrityValidationError(
            "adversarial integrity hash mismatch"
        )
    if equivalence.get("equivalent") is not True:
        raise AdversarialIntegrityValidationError(
            "adversarial integrity equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise AdversarialIntegrityValidationError(
                f"missing adversarial integrity scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise AdversarialIntegrityValidationError(
                f"adversarial integrity scenario mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise AdversarialIntegrityValidationError(
                f"adversarial integrity scenario not verified: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AdversarialIntegrityValidationError(f"report must be object: {path}")
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
    except AdversarialIntegrityValidationError as exc:
        print(f"Adversarial integrity validation FAILED: {exc}")
        return 1

    print(
        "Adversarial integrity validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"adversarial_integrity_hash={report.adversarial_integrity_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

