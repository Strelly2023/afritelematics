"""Validate the controlled AfriRide live pilot protocol."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.live_pilot_protocol import (
    AUTHORITY_BOUNDARY,
    NON_CLAIMS,
    REQUIRED_OUTPUTS,
    REQUIRED_SCENARIOS,
    LivePilotProtocolError,
    build_live_pilot_protocol,
)


class AfriRideLivePilotProtocolValidationError(RuntimeError):
    """Raised when the live pilot protocol leaves its bounded scope."""


@dataclass(frozen=True)
class AfriRideLivePilotProtocolValidationReport:
    protocol_hash: str
    required_scenarios: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return len(self.protocol_hash) == 64 and self.required_scenarios == REQUIRED_SCENARIOS

    def canonical_dict(self) -> dict[str, object]:
        return {
            "protocol_hash": self.protocol_hash,
            "required_scenarios": list(self.required_scenarios),
            "schema": "afriride.live_pilot_protocol_validation_report.v1",
            "verified": self.verified,
        }

    def validation_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> AfriRideLivePilotProtocolValidationReport:
    try:
        protocol = build_live_pilot_protocol()
    except LivePilotProtocolError as exc:
        raise AfriRideLivePilotProtocolValidationError(str(exc)) from exc

    payload = protocol.canonical_dict()
    _validate_payload(payload)
    report = AfriRideLivePilotProtocolValidationReport(
        protocol_hash=str(payload["protocol_hash"]),
        required_scenarios=tuple(payload["scenario_scripts"][index]["scenario"] for index in range(5)),
    )
    if not report.verified:
        raise AfriRideLivePilotProtocolValidationError("live pilot protocol not verified")
    return report


def validate_report_file(
    path: Path = Path("reports/afriride_live_pilot_protocol_v1/live_pilot_protocol.json"),
) -> None:
    if not path.exists():
        raise AfriRideLivePilotProtocolValidationError("missing live pilot protocol report")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = build_live_pilot_protocol().canonical_dict()
    if payload.get("protocol_hash") != expected.get("protocol_hash"):
        raise AfriRideLivePilotProtocolValidationError("live pilot protocol hash mismatch")
    _validate_payload(payload)


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("authority_boundary") != AUTHORITY_BOUNDARY:
        raise AfriRideLivePilotProtocolValidationError("authority boundary mismatch")

    scale = payload.get("scale")
    if not isinstance(scale, dict):
        raise AfriRideLivePilotProtocolValidationError("pilot scale missing")
    if scale.get("drivers_min") != 5 or scale.get("drivers_max") != 20:
        raise AfriRideLivePilotProtocolValidationError("pilot must remain 5-20 drivers")

    claim_boundary = payload.get("claim_boundary")
    if not isinstance(claim_boundary, dict):
        raise AfriRideLivePilotProtocolValidationError("claim boundary missing")
    non_claims = tuple(claim_boundary.get("non_claims", ()))
    if set(NON_CLAIMS).difference(non_claims):
        raise AfriRideLivePilotProtocolValidationError("live pilot non-claims incomplete")

    scenario_scripts = payload.get("scenario_scripts")
    if not isinstance(scenario_scripts, (list, tuple)):
        raise AfriRideLivePilotProtocolValidationError("scenario scripts missing")
    scenarios = tuple(script.get("scenario") for script in scenario_scripts)
    if scenarios != REQUIRED_SCENARIOS:
        raise AfriRideLivePilotProtocolValidationError("scenario scripts incomplete")

    outputs = tuple(payload.get("evidence_outputs", ()))
    if outputs != REQUIRED_OUTPUTS:
        raise AfriRideLivePilotProtocolValidationError("evidence outputs incomplete")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise AfriRideLivePilotProtocolValidationError("metrics missing")
    for metric in (
        "replay_equivalence_rate",
        "trace_completeness_rate",
        "dispute_reproducibility_rate",
    ):
        if metrics.get(metric) != 1.0:
            raise AfriRideLivePilotProtocolValidationError(f"{metric} must target 1.0")
    for metric in (
        "admissibility_divergence",
        "authentication_bypass",
        "identity_divergence",
        "pricing_deviation",
    ):
        if metrics.get(metric) != 0:
            raise AfriRideLivePilotProtocolValidationError(f"{metric} must target 0")

    stop_conditions = tuple(payload.get("stop_conditions", ()))
    for required in (
        "replay mismatch",
        "manual truth override attempted",
        "pilot scope escape",
    ):
        if required not in stop_conditions:
            raise AfriRideLivePilotProtocolValidationError(
                f"missing stop condition: {required}"
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
    except AfriRideLivePilotProtocolValidationError as exc:
        print(f"AfriRide live pilot protocol validation FAILED: {exc}")
        return 1

    print(
        "AfriRide live pilot protocol validation PASSED: "
        f"protocol_hash={report.protocol_hash} "
        f"validation_hash={report.validation_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
