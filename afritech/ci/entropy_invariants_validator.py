"""Validate entropy-bound execution invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.runtime.entropy.proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    EntropyProofError,
    EntropyProofReport,
    run_entropy_bound_execution_proof,
)


class EntropyInvariantsValidationError(RuntimeError):
    """Raised when entropy-bound execution validation fails."""


@dataclass(frozen=True)
class EntropyInvariantsValidationReport:
    scenarios: tuple[str, ...]
    replay_hashes: tuple[str, ...]
    report_hash: str

    @property
    def verified(self) -> bool:
        return (
            self.scenarios == REQUIRED_SCENARIOS
            and all(len(value) == 64 for value in self.replay_hashes)
            and len(self.report_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "report_hash": self.report_hash,
            "replay_hashes": list(self.replay_hashes),
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.entropy_invariants_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> EntropyInvariantsValidationReport:
    try:
        proof = run_entropy_bound_execution_proof()
    except EntropyProofError as exc:
        raise EntropyInvariantsValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = EntropyInvariantsValidationReport(
        replay_hashes=tuple(
            scenario.disturbed.replay_hash for scenario in proof.scenarios
        ),
        report_hash=proof.report_hash(),
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise EntropyInvariantsValidationError("entropy invariant report failed")
    return report


def _validate_proof(proof: EntropyProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise EntropyInvariantsValidationError("entropy scenario set mismatch")
    for scenario in proof.scenarios:
        if not scenario.same_replay_hash:
            raise EntropyInvariantsValidationError(
                f"replay hash drift under entropy: {scenario.scenario}"
            )
        if not scenario.same_identity_resolution:
            raise EntropyInvariantsValidationError(
                f"identity resolution drift under entropy: {scenario.scenario}"
            )
        if not scenario.same_admissibility_decision:
            raise EntropyInvariantsValidationError(
                f"admissibility drift under entropy: {scenario.scenario}"
            )
        if not scenario.same_convergence_result:
            raise EntropyInvariantsValidationError(
                f"convergence drift under entropy: {scenario.scenario}"
            )


def _validate_report_files(
    proof: EntropyProofReport,
    report_dir: Path = Path("reports/entropy_proof_v1"),
) -> None:
    equivalence_path = report_dir / "replay_equivalence_report.json"
    if not equivalence_path.exists():
        raise EntropyInvariantsValidationError(
            "missing entropy replay equivalence report"
        )
    equivalence = _load_json(equivalence_path)
    if equivalence.get("report_hash") != proof.report_hash():
        raise EntropyInvariantsValidationError(
            "entropy replay equivalence report hash mismatch"
        )
    if equivalence.get("equivalent") is not True:
        raise EntropyInvariantsValidationError(
            "entropy replay equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise EntropyInvariantsValidationError(
                f"missing entropy scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise EntropyInvariantsValidationError(
                f"entropy scenario report name mismatch: {filename}"
            )
        if payload.get("equivalent") is not True:
            raise EntropyInvariantsValidationError(
                f"entropy scenario report not equivalent: {filename}"
            )
        if payload.get("replay_hash") != scenario.disturbed.replay_hash:
            raise EntropyInvariantsValidationError(
                f"entropy scenario replay hash mismatch: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EntropyInvariantsValidationError(f"report must be object: {path}")
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
    except EntropyInvariantsValidationError as exc:
        print(f"Entropy-bound execution validation FAILED: {exc}")
        return 1

    print(
        "Entropy-bound execution validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"report_hash={report.report_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
