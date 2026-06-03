"""Validate trust lock-in proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.trust_lock.engine.proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    TrustLockProofError,
    TrustLockProofReport,
    run_trust_lock_proof,
)


class TrustLockValidationError(RuntimeError):
    """Raised when trust lock validation fails."""


@dataclass(frozen=True)
class TrustLockValidationReport:
    scenarios: tuple[str, ...]
    trust_lock_hash: str

    @property
    def verified(self) -> bool:
        return self.scenarios == REQUIRED_SCENARIOS and len(self.trust_lock_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.trust_lock_validation_report.v1",
            "trust_lock_hash": self.trust_lock_hash,
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> TrustLockValidationReport:
    try:
        proof = run_trust_lock_proof()
    except TrustLockProofError as exc:
        raise TrustLockValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = TrustLockValidationReport(
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
        trust_lock_hash=proof.trust_lock_hash,
    )
    if not report.verified:
        raise TrustLockValidationError("trust lock validation report failed")
    return report


def _validate_proof(proof: TrustLockProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise TrustLockValidationError("trust lock scenario set mismatch")
    for scenario in proof.scenarios:
        simulation = scenario.simulation
        if not scenario.verified:
            raise TrustLockValidationError(
                f"trust lock scenario failed: {scenario.scenario}"
            )
        if not simulation.baseline_trusted:
            raise TrustLockValidationError("baseline external workflows do not trust evidence")
        if not simulation.removal_breaks_workflows:
            raise TrustLockValidationError("removal did not break dependent workflows")
        if not simulation.replacement_breaks_trust:
            raise TrustLockValidationError("replacement did not break trust")


def _validate_report_files(
    proof: TrustLockProofReport,
    report_dir: Path = Path("reports/trust_lock_proof_v1"),
) -> None:
    equivalence_path = report_dir / "trust_lock_equivalence.json"
    if not equivalence_path.exists():
        raise TrustLockValidationError("missing trust lock equivalence report")
    equivalence = _load_json(equivalence_path)
    if equivalence.get("trust_lock_hash") != proof.trust_lock_hash:
        raise TrustLockValidationError("trust lock hash mismatch")
    if equivalence.get("equivalent") is not True:
        raise TrustLockValidationError("trust lock equivalence report is not equivalent")

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise TrustLockValidationError(
                f"missing trust lock scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise TrustLockValidationError(
                f"trust lock scenario mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise TrustLockValidationError(
                f"trust lock scenario not verified: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TrustLockValidationError(f"report must be object: {path}")
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
    except TrustLockValidationError as exc:
        print(f"Trust lock validation FAILED: {exc}")
        return 1

    print(
        "Trust lock validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"trust_lock_hash={report.trust_lock_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

