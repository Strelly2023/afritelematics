"""Validate the AfriRide post-pilot evidence analysis protocol."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.post_pilot_analysis import (
    ANALYSIS_BOUNDARY,
    NON_CLAIMS,
    REQUIRED_ANALYSIS_GATES,
    REQUIRED_DECISIONS,
    PostPilotAnalysisError,
    build_post_pilot_analysis_protocol,
)


class AfriRidePostPilotAnalysisValidationError(RuntimeError):
    """Raised when post-pilot analysis exceeds its bounded scope."""


@dataclass(frozen=True)
class AfriRidePostPilotAnalysisValidationReport:
    analysis_hash: str
    runbook_hash: str

    @property
    def verified(self) -> bool:
        return len(self.analysis_hash) == 64 and len(self.runbook_hash) == 64

    def canonical_dict(self) -> dict[str, object]:
        return {
            "analysis_hash": self.analysis_hash,
            "runbook_hash": self.runbook_hash,
            "schema": "afriride.post_pilot_analysis_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRidePostPilotAnalysisValidationReport:
    try:
        protocol = build_post_pilot_analysis_protocol()
    except PostPilotAnalysisError as exc:
        raise AfriRidePostPilotAnalysisValidationError(str(exc)) from exc

    payload = protocol.canonical_dict()
    _validate_payload(payload)
    report = AfriRidePostPilotAnalysisValidationReport(
        analysis_hash=str(payload["analysis_hash"]),
        runbook_hash=str(payload["runbook_hash"]),
    )
    if not report.verified:
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot analysis protocol not verified"
        )
    return report


def validate_report_file(
    path: Path = Path("reports/afriride_live_pilot_protocol_v1/post_pilot_analysis.json"),
) -> None:
    if not path.exists():
        raise AfriRidePostPilotAnalysisValidationError(
            "missing post-pilot analysis report"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_post_pilot_analysis_protocol().canonical_dict()
    if payload.get("analysis_hash") != expected.get("analysis_hash"):
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot analysis hash mismatch"
        )
    _validate_payload(payload)


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("authority_boundary") != ANALYSIS_BOUNDARY:
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot authority boundary mismatch"
        )
    if tuple(payload.get("decisions", ())) != REQUIRED_DECISIONS:
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot decision set mismatch"
        )
    if set(NON_CLAIMS).difference(tuple(payload.get("non_claims", ()))): 
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot non-claims incomplete"
        )

    gates = payload.get("gates")
    if not isinstance(gates, list):
        raise AfriRidePostPilotAnalysisValidationError("post-pilot gates missing")
    gate_names = tuple(gate.get("name") for gate in gates)
    if gate_names != REQUIRED_ANALYSIS_GATES:
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot gates incomplete"
        )

    failure_actions = tuple(str(gate.get("failure_action", "")) for gate in gates)
    if not any(action.startswith("defer") for action in failure_actions):
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot analysis must support deferral"
        )
    if not any(action.startswith("reject") for action in failure_actions):
        raise AfriRidePostPilotAnalysisValidationError(
            "post-pilot analysis must support rejection"
        )

    pass_conditions = " ".join(str(gate.get("pass_condition", "")) for gate in gates)
    for required in (
        "replay",
        "identity",
        "pricing",
        "admissibility",
        "dispute",
        "dashboard",
    ):
        if required not in pass_conditions:
            raise AfriRidePostPilotAnalysisValidationError(
                f"post-pilot analysis missing pass condition: {required}"
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
    except AfriRidePostPilotAnalysisValidationError as exc:
        print(f"AfriRide post-pilot analysis validation FAILED: {exc}")
        return 1

    print(
        "AfriRide post-pilot analysis validation PASSED: "
        f"analysis_hash={report.analysis_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
