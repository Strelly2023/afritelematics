"""Validate AfriRide marketplace realism proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from ecosystems.afriride.simulation.marketplace_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_REJECTIONS,
    REQUIRED_SCENARIOS,
    MarketplaceProofError,
    run_marketplace_proof,
)


class MarketplaceSimulationValidationError(RuntimeError):
    """Raised when marketplace simulation proof fails."""


@dataclass(frozen=True)
class MarketplaceSimulationValidationReport:
    scenario_count: int
    rejected_authority_cases: tuple[str, ...]
    market_replay_hash: str
    partition_order_hash: str
    proof_report_hash: str
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.scenario_count == len(REQUIRED_SCENARIOS)
            and self.rejected_authority_cases == REQUIRED_REJECTIONS
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and all(
                len(value) == 64
                for value in (
                    self.market_replay_hash,
                    self.partition_order_hash,
                    self.proof_report_hash,
                )
            )
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "market_replay_hash": self.market_replay_hash,
            "partition_order_hash": self.partition_order_hash,
            "proof_report_hash": self.proof_report_hash,
            "rejected_authority_cases": list(self.rejected_authority_cases),
            "scenario_count": self.scenario_count,
            "schema": "afritech.marketplace_simulation_validation_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> MarketplaceSimulationValidationReport:
    report = run_marketplace_simulation_validation()
    if not report.verified:
        raise MarketplaceSimulationValidationError("marketplace simulation validation failed")
    return report


def run_marketplace_simulation_validation() -> MarketplaceSimulationValidationReport:
    try:
        proof = run_marketplace_proof()
    except MarketplaceProofError as exc:
        raise MarketplaceSimulationValidationError(str(exc)) from exc

    if not proof.verified:
        raise MarketplaceSimulationValidationError("marketplace proof failed")

    return MarketplaceSimulationValidationReport(
        authority_disclaimer=proof.authority_disclaimer,
        market_replay_hash=proof.market_replay_hash,
        partition_order_hash=proof.partition_order_hash,
        proof_report_hash=proof.report_hash(),
        rejected_authority_cases=proof.rejected_authority_cases,
        scenario_count=len(proof.scenarios),
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
    except MarketplaceSimulationValidationError as exc:
        print(f"Marketplace simulation validation FAILED: {exc}")
        return 1
    print(
        "Marketplace simulation validation PASSED: "
        f"scenarios={report.scenario_count} "
        f"market_replay_hash={report.market_replay_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

