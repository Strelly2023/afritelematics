"""Validate economic trust proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.payments.economic_trust_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_PROOFS,
    REQUIRED_REJECTIONS,
    EconomicTrustProofError,
    run_economic_trust_proof,
)


class EconomicTrustValidationError(RuntimeError):
    """Raised when economic trust validation fails."""


@dataclass(frozen=True)
class EconomicTrustValidationReport:
    proof_names: tuple[str, ...]
    rejected_cases: tuple[str, ...]
    economic_replay_hash: str
    proof_report_hash: str
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.proof_names == REQUIRED_PROOFS
            and self.rejected_cases == REQUIRED_REJECTIONS
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and len(self.economic_replay_hash) == 64
            and len(self.proof_report_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "economic_replay_hash": self.economic_replay_hash,
            "proof_names": list(self.proof_names),
            "proof_report_hash": self.proof_report_hash,
            "rejected_cases": list(self.rejected_cases),
            "schema": "afritech.economic_trust_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> EconomicTrustValidationReport:
    report = run_economic_trust_validation()
    if not report.verified:
        raise EconomicTrustValidationError("economic trust validation failed")
    return report


def run_economic_trust_validation() -> EconomicTrustValidationReport:
    try:
        proof = run_economic_trust_proof()
    except EconomicTrustProofError as exc:
        raise EconomicTrustValidationError(str(exc)) from exc

    if not proof.verified:
        raise EconomicTrustValidationError("economic trust proof failed")

    return EconomicTrustValidationReport(
        authority_disclaimer=proof.authority_disclaimer,
        economic_replay_hash=proof.economic_replay_hash,
        proof_names=proof.proof_names,
        proof_report_hash=proof.report_hash(),
        rejected_cases=proof.rejected_cases,
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
    except EconomicTrustValidationError as exc:
        print(f"Economic trust validation FAILED: {exc}")
        return 1
    print(
        "Economic trust validation PASSED: "
        f"economic_replay_hash={report.economic_replay_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
