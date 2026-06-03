"""Validate adversarial security proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.security.adversarial_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_ATTACKS,
    SecurityAdversarialProofError,
    run_security_adversarial_proof,
)


class SecurityAdversarialValidationError(RuntimeError):
    """Raised when adversarial security proof fails."""


@dataclass(frozen=True)
class SecurityAdversarialValidationReport:
    attack_count: int
    rejected_attacks: tuple[str, ...]
    baseline_replay_hash: str
    proof_report_hash: str
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.attack_count == len(REQUIRED_ATTACKS)
            and self.rejected_attacks == REQUIRED_ATTACKS
            and len(self.baseline_replay_hash) == 64
            and len(self.proof_report_hash) == 64
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "attack_count": self.attack_count,
            "authority_disclaimer": self.authority_disclaimer,
            "baseline_replay_hash": self.baseline_replay_hash,
            "proof_report_hash": self.proof_report_hash,
            "rejected_attacks": list(self.rejected_attacks),
            "schema": "afritech.security_adversarial_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> SecurityAdversarialValidationReport:
    report = run_security_adversarial_validation()
    if not report.verified:
        raise SecurityAdversarialValidationError("security adversarial validation failed")
    return report


def run_security_adversarial_validation() -> SecurityAdversarialValidationReport:
    try:
        proof = run_security_adversarial_proof()
    except SecurityAdversarialProofError as exc:
        raise SecurityAdversarialValidationError(str(exc)) from exc

    if not proof.verified:
        raise SecurityAdversarialValidationError("security adversarial proof failed")

    rejected_attacks = tuple(
        evidence.attack_name
        for evidence in proof.attacks
        if evidence.disposition == "rejected"
    )
    return SecurityAdversarialValidationReport(
        attack_count=len(proof.attacks),
        authority_disclaimer=proof.authority_disclaimer,
        baseline_replay_hash=proof.baseline_replay_hash,
        proof_report_hash=proof.report_hash(),
        rejected_attacks=rejected_attacks,
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
        report = validate()
    except SecurityAdversarialValidationError as exc:
        print(f"Security adversarial validation FAILED: {exc}")
        return 1
    print(
        "Security adversarial validation PASSED: "
        f"attacks={report.attack_count} "
        f"baseline_replay_hash={report.baseline_replay_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

