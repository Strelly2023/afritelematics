"""Validate the AfriRide day-one pilot runbook."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.day_one_runbook import (
    EVIDENCE_CHECKPOINTS,
    NON_CLAIMS,
    RUNBOOK_BOUNDARY,
    DayOneRunbookError,
    build_day_one_runbook,
)
from afriride.field_validation.live_pilot_protocol import REQUIRED_SCENARIOS


class AfriRideDayOneRunbookValidationError(RuntimeError):
    """Raised when the day-one runbook violates pilot boundaries."""


@dataclass(frozen=True)
class AfriRideDayOneRunbookValidationReport:
    runbook_hash: str
    protocol_hash: str

    @property
    def verified(self) -> bool:
        return len(self.runbook_hash) == 64 and len(self.protocol_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "protocol_hash": self.protocol_hash,
            "runbook_hash": self.runbook_hash,
            "schema": "afriride.day_one_runbook_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRideDayOneRunbookValidationReport:
    try:
        runbook = build_day_one_runbook()
    except DayOneRunbookError as exc:
        raise AfriRideDayOneRunbookValidationError(str(exc)) from exc

    payload = runbook.canonical_dict()
    _validate_payload(payload)
    report = AfriRideDayOneRunbookValidationReport(
        protocol_hash=str(payload["protocol_hash"]),
        runbook_hash=str(payload["runbook_hash"]),
    )
    if not report.verified:
        raise AfriRideDayOneRunbookValidationError("day-one runbook not verified")
    return report


def validate_report_file(
    path: Path = Path("reports/afriride_live_pilot_protocol_v1/day_one_runbook.json"),
) -> None:
    if not path.exists():
        raise AfriRideDayOneRunbookValidationError("missing day-one runbook report")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_day_one_runbook().canonical_dict()
    if payload.get("runbook_hash") != expected.get("runbook_hash"):
        raise AfriRideDayOneRunbookValidationError("day-one runbook hash mismatch")
    _validate_payload(payload)


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("authority_boundary") != RUNBOOK_BOUNDARY:
        raise AfriRideDayOneRunbookValidationError("runbook authority boundary mismatch")
    if set(NON_CLAIMS).difference(tuple(payload.get("non_claims", ()))): 
        raise AfriRideDayOneRunbookValidationError("runbook non-claims incomplete")
    if tuple(payload.get("required_scenarios", ())) != REQUIRED_SCENARIOS:
        raise AfriRideDayOneRunbookValidationError("runbook scenario set mismatch")
    if tuple(payload.get("required_evidence_checkpoints", ())) != EVIDENCE_CHECKPOINTS:
        raise AfriRideDayOneRunbookValidationError("runbook evidence set mismatch")

    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise AfriRideDayOneRunbookValidationError("runbook steps missing")
    minutes = tuple(step.get("minute") for step in steps)
    if minutes != tuple(sorted(minutes)):
        raise AfriRideDayOneRunbookValidationError("runbook timeline not ordered")
    if minutes[0] != 0 or minutes[-1] != 240:
        raise AfriRideDayOneRunbookValidationError("runbook must cover minute 0 to 240")

    evidence = {
        evidence_item
        for step in steps
        for evidence_item in step.get("evidence", ())
    }
    missing = set(EVIDENCE_CHECKPOINTS).difference(evidence)
    if missing:
        raise AfriRideDayOneRunbookValidationError(
            f"runbook missing evidence: {tuple(sorted(missing))}"
        )

    stop_checks = tuple(str(step.get("stop_check", "")) for step in steps)
    for required in (
        "validator fails",
        "duplicate execution",
        "replay authority",
        "non-claim is violated",
    ):
        if not any(required in stop_check for stop_check in stop_checks):
            raise AfriRideDayOneRunbookValidationError(
                f"runbook missing stop check: {required}"
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
    except AfriRideDayOneRunbookValidationError as exc:
        print(f"AfriRide day-one runbook validation FAILED: {exc}")
        return 1

    print(
        "AfriRide day-one runbook validation PASSED: "
        f"runbook_hash={report.runbook_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
