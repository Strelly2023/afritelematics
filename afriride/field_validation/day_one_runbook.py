"""Day-one controlled pilot runbook for AfriRide.

The runbook describes how the first controlled pilot day may be operated. It
does not assert that the pilot has occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.live_pilot_protocol import (
    AUTHORITY_BOUNDARY as PILOT_PROTOCOL_BOUNDARY,
    REQUIRED_SCENARIOS,
    build_live_pilot_protocol,
)


RUNBOOK_BOUNDARY = (
    "The day-one runbook coordinates controlled pilot execution only. It does "
    "not define replay truth, certify pilot completion, or authorize production "
    "readiness."
)

ALLOWED_CLAIM = (
    "AfriRide has a governed first-day execution script for collecting bounded "
    "pilot evidence."
)

NON_CLAIMS = (
    "pilot_completed",
    "production_ready",
    "public_launch_ready",
    "regulatory_approved",
    "market_validated",
)

EVIDENCE_CHECKPOINTS = (
    "device_registration_snapshot",
    "preflight_validator_receipt",
    "dry_run_trace_receipt",
    "offline_trip_trace",
    "delayed_sync_trace",
    "gps_drift_trace",
    "duplicate_events_trace",
    "dispute_resolution_trace",
    "proof_dashboard_snapshot",
    "pilot_controller_closeout",
)


class DayOneRunbookError(ValueError):
    """Raised when the day-one runbook breaks pilot governance."""


@dataclass(frozen=True)
class RunbookStep:
    minute: int
    owner: str
    action: str
    evidence: tuple[str, ...]
    stop_check: str

    def __post_init__(self) -> None:
        if self.minute < 0:
            raise DayOneRunbookError("runbook minutes must be non-negative")
        if not self.owner:
            raise DayOneRunbookError("runbook step owner is required")
        if not self.action:
            raise DayOneRunbookError("runbook step action is required")
        if not self.stop_check:
            raise DayOneRunbookError("runbook step stop check is required")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "evidence": list(self.evidence),
            "minute": self.minute,
            "owner": self.owner,
            "stop_check": self.stop_check,
        }


@dataclass(frozen=True)
class DayOneRunbook:
    protocol_hash: str
    steps: tuple[RunbookStep, ...]
    authority_boundary: str = RUNBOOK_BOUNDARY
    allowed_claim: str = ALLOWED_CLAIM
    non_claims: tuple[str, ...] = NON_CLAIMS

    def __post_init__(self) -> None:
        if self.authority_boundary != RUNBOOK_BOUNDARY:
            raise DayOneRunbookError("runbook authority boundary mismatch")
        if self.allowed_claim != ALLOWED_CLAIM:
            raise DayOneRunbookError("runbook allowed claim mismatch")
        if set(NON_CLAIMS).difference(self.non_claims):
            raise DayOneRunbookError("runbook non-claims incomplete")
        if len(self.protocol_hash) != 64:
            raise DayOneRunbookError("runbook requires protocol hash")
        minutes = tuple(step.minute for step in self.steps)
        if minutes != tuple(sorted(minutes)):
            raise DayOneRunbookError("runbook steps must be minute ordered")
        evidence = {
            item
            for step in self.steps
            for item in step.evidence
        }
        missing = set(EVIDENCE_CHECKPOINTS).difference(evidence)
        if missing:
            raise DayOneRunbookError(
                f"runbook missing evidence checkpoints: {tuple(sorted(missing))}"
            )
        scenario_names = {scenario for scenario in REQUIRED_SCENARIOS}
        scenario_evidence = {
            item.removesuffix("_trace")
            for item in evidence
            if item.endswith("_trace")
        }
        if scenario_names.difference(scenario_evidence):
            raise DayOneRunbookError("runbook does not cover every required scenario")

    @property
    def runbook_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "allowed_claim": self.allowed_claim,
            "authority_boundary": self.authority_boundary,
            "non_claims": list(self.non_claims),
            "pilot_protocol_boundary": PILOT_PROTOCOL_BOUNDARY,
            "protocol_hash": self.protocol_hash,
            "required_evidence_checkpoints": list(EVIDENCE_CHECKPOINTS),
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "schema": "afriride.day_one_runbook.v1",
            "steps": [step.canonical_dict() for step in self.steps],
        }
        if include_hash:
            payload["runbook_hash"] = self.runbook_hash
        return payload


def build_day_one_runbook() -> DayOneRunbook:
    protocol = build_live_pilot_protocol()
    return DayOneRunbook(
        protocol_hash=protocol.protocol_hash,
        steps=(
            RunbookStep(
                minute=0,
                owner="pilot_controller",
                action="Open pilot window and restate claim boundary to all roles.",
                evidence=("pilot_controller_closeout",),
                stop_check="stop if any participant treats runbook as production authority",
            ),
            RunbookStep(
                minute=15,
                owner="proof_operator",
                action="Register devices and capture signed device roster snapshot.",
                evidence=("device_registration_snapshot",),
                stop_check="stop if any driver or rider device is unbound or unsigned",
            ),
            RunbookStep(
                minute=30,
                owner="proof_operator",
                action="Run preflight validators before any field movement begins.",
                evidence=("preflight_validator_receipt",),
                stop_check="stop if any validator fails",
            ),
            RunbookStep(
                minute=45,
                owner="pilot_controller",
                action="Execute dry-run trip with stationary devices and replay the trace.",
                evidence=("dry_run_trace_receipt",),
                stop_check="stop if replay readiness is not ready",
            ),
            RunbookStep(
                minute=75,
                owner="driver_cohort",
                action="Run offline trip script with controlled disconnect and reconnect.",
                evidence=("offline_trip_trace",),
                stop_check="stop if buffered events cannot replay equivalently",
            ),
            RunbookStep(
                minute=105,
                owner="proof_operator",
                action="Run delayed sync script and replay late-arriving events.",
                evidence=("delayed_sync_trace",),
                stop_check="stop if canonical replay changes final truth",
            ),
            RunbookStep(
                minute=135,
                owner="driver_cohort",
                action="Collect GPS drift observations along the bounded route.",
                evidence=("gps_drift_trace",),
                stop_check="stop if GPS normalization changes pricing truth",
            ),
            RunbookStep(
                minute=165,
                owner="proof_operator",
                action="Submit duplicate signed event batches and verify idempotence.",
                evidence=("duplicate_events_trace",),
                stop_check="stop if duplicate delivery causes duplicate execution",
            ),
            RunbookStep(
                minute=195,
                owner="support_operator",
                action="Run dispute drill through replay authority with no manual override.",
                evidence=("dispute_resolution_trace",),
                stop_check="stop if support outcome diverges from replay authority",
            ),
            RunbookStep(
                minute=225,
                owner="proof_operator",
                action="Generate proof dashboard snapshot from collected pilot traces.",
                evidence=("proof_dashboard_snapshot",),
                stop_check="stop if dashboard reports drift or missing evidence",
            ),
            RunbookStep(
                minute=240,
                owner="pilot_controller",
                action="Close pilot window and record no-claim escalation decision.",
                evidence=("pilot_controller_closeout",),
                stop_check="stop external reporting if any non-claim is violated",
            ),
        ),
    )


def write_day_one_runbook(
    output_path: str | Path = "reports/afriride_live_pilot_protocol_v1/day_one_runbook.json",
) -> DayOneRunbook:
    runbook = build_day_one_runbook()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(runbook.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return runbook


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
