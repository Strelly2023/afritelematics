"""Validate AfriRide mobile pilot end-to-end proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from ecosystems.afriride.simulation.mobile_pilot_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_REJECTIONS,
    MobilePilotProofError,
    run_mobile_pilot_e2e_proof,
)


class MobilePilotE2EValidationError(RuntimeError):
    """Raised when mobile pilot proof fails."""


@dataclass(frozen=True)
class MobilePilotE2EValidationReport:
    event_count: int
    trip_replay_hash: str
    replayed_trip_hash: str
    persistent_event_hash: str
    rejected_cases: tuple[str, ...]
    proof_report_hash: str
    authority_disclaimer: str

    @property
    def verified(self) -> bool:
        return (
            self.event_count >= 6
            and self.trip_replay_hash == self.replayed_trip_hash
            and self.rejected_cases == REQUIRED_REJECTIONS
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and all(
                len(value) == 64
                for value in (
                    self.trip_replay_hash,
                    self.replayed_trip_hash,
                    self.persistent_event_hash,
                    self.proof_report_hash,
                )
            )
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "event_count": self.event_count,
            "persistent_event_hash": self.persistent_event_hash,
            "proof_report_hash": self.proof_report_hash,
            "rejected_cases": list(self.rejected_cases),
            "replayed_trip_hash": self.replayed_trip_hash,
            "schema": "afritech.mobile_pilot_e2e_validation_report.v1",
            "trip_replay_hash": self.trip_replay_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> MobilePilotE2EValidationReport:
    report = run_mobile_pilot_e2e_validation()
    if not report.verified:
        raise MobilePilotE2EValidationError("mobile pilot e2e validation failed")
    return report


def run_mobile_pilot_e2e_validation() -> MobilePilotE2EValidationReport:
    try:
        proof = run_mobile_pilot_e2e_proof()
    except MobilePilotProofError as exc:
        raise MobilePilotE2EValidationError(str(exc)) from exc

    if not proof.verified:
        raise MobilePilotE2EValidationError("mobile pilot e2e proof failed")

    return MobilePilotE2EValidationReport(
        authority_disclaimer=proof.authority_disclaimer,
        event_count=proof.event_count,
        persistent_event_hash=proof.persistent_event_hash,
        proof_report_hash=proof.report_hash(),
        rejected_cases=proof.rejected_cases,
        replayed_trip_hash=proof.replayed_trip_hash,
        trip_replay_hash=proof.trip_replay_hash,
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
    except MobilePilotE2EValidationError as exc:
        print(f"Mobile pilot E2E validation FAILED: {exc}")
        return 1
    print(
        "Mobile pilot E2E validation PASSED: "
        f"event_count={report.event_count} "
        f"trip_replay_hash={report.trip_replay_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
