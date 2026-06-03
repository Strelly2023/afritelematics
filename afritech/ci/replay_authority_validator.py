"""Validate replay authority proof invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afritech.replay_authority.engine.proof import (
    REPORT_FILES,
    REQUIRED_SCENARIOS,
    ReplayAuthorityProofError,
    ReplayAuthorityProofReport,
    run_replay_authority_proof,
)


class ReplayAuthorityValidationError(RuntimeError):
    """Raised when replay authority validation fails."""


@dataclass(frozen=True)
class ReplayAuthorityValidationReport:
    scenarios: tuple[str, ...]
    replay_authority_hash: str

    @property
    def verified(self) -> bool:
        return self.scenarios == REQUIRED_SCENARIOS and len(self.replay_authority_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "replay_authority_hash": self.replay_authority_hash,
            "scenario_count": len(self.scenarios),
            "scenarios": list(self.scenarios),
            "schema": "afritech.replay_authority_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> ReplayAuthorityValidationReport:
    try:
        proof = run_replay_authority_proof()
    except ReplayAuthorityProofError as exc:
        raise ReplayAuthorityValidationError(str(exc)) from exc

    _validate_proof(proof)
    _validate_report_files(proof)
    report = ReplayAuthorityValidationReport(
        replay_authority_hash=proof.replay_authority_hash,
        scenarios=tuple(scenario.scenario for scenario in proof.scenarios),
    )
    if not report.verified:
        raise ReplayAuthorityValidationError("replay authority report failed")
    return report


def _validate_proof(proof: ReplayAuthorityProofReport) -> None:
    if tuple(scenario.scenario for scenario in proof.scenarios) != REQUIRED_SCENARIOS:
        raise ReplayAuthorityValidationError("replay authority scenario set mismatch")
    for scenario in proof.scenarios:
        if not scenario.same_replay_authority:
            raise ReplayAuthorityValidationError(
                f"replay authority drift: {scenario.scenario}"
            )
        if not scenario.same_resolution:
            raise ReplayAuthorityValidationError(
                f"dispute resolution drift: {scenario.scenario}"
            )
        if not scenario.conflicting_claims_resolved:
            raise ReplayAuthorityValidationError("conflicting claims not resolved")


def _validate_report_files(
    proof: ReplayAuthorityProofReport,
    report_dir: Path = Path("reports/replay_authority_proof_v1"),
) -> None:
    equivalence_path = report_dir / "replay_authority_equivalence.json"
    if not equivalence_path.exists():
        raise ReplayAuthorityValidationError("missing replay authority equivalence report")
    equivalence = _load_json(equivalence_path)
    if equivalence.get("replay_authority_hash") != proof.replay_authority_hash:
        raise ReplayAuthorityValidationError("replay authority hash mismatch")
    if equivalence.get("equivalent") is not True:
        raise ReplayAuthorityValidationError(
            "replay authority equivalence report is not equivalent"
        )

    scenarios = {scenario.scenario: scenario for scenario in proof.scenarios}
    for scenario_name, filename in REPORT_FILES.items():
        path = report_dir / filename
        if not path.exists():
            raise ReplayAuthorityValidationError(
                f"missing replay authority scenario report: {filename}"
            )
        payload = _load_json(path)
        scenario = scenarios[scenario_name]
        if payload.get("scenario") != scenario.scenario:
            raise ReplayAuthorityValidationError(
                f"replay authority scenario mismatch: {filename}"
            )
        if payload.get("verified") is not True:
            raise ReplayAuthorityValidationError(
                f"replay authority scenario not verified: {filename}"
            )
        packet = payload.get("audit_packet")
        if not isinstance(packet, dict) or len(str(packet.get("audit_hash", ""))) != 64:
            raise ReplayAuthorityValidationError(
                f"missing audit hash in replay authority report: {filename}"
            )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReplayAuthorityValidationError(f"report must be object: {path}")
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
    except ReplayAuthorityValidationError as exc:
        print(f"Replay authority validation FAILED: {exc}")
        return 1

    print(
        "Replay authority validation PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"replay_authority_hash={report.replay_authority_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

