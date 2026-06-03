"""Validate the AfriRide GA Elite pilot rollout strategy contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_GA_ELITE_PILOT_ROLLOUT_STRATEGY.md"

ROLLOUT_LAW = ("execution", "evidence", "replay", "verification", "certification", "expansion")
FORBIDDEN_LAW = ("expansion", "hope", "evidence_later")


class AfriRideGAElitePilotRolloutStrategyValidationError(RuntimeError):
    """Raised when the rollout strategy contract is invalid."""


@dataclass(frozen=True)
class AfriRideGAElitePilotRolloutStrategyReport:
    schema: str
    status: str
    classification: str
    field_evidence_pending: bool
    wave7_authorized: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.ga_elite_pilot_rollout_strategy.v1"
            and self.status == "ga_elite_pilot_rollout_strategy_contract"
            and self.classification == "evidence_governed_expansion_plan"
            and self.field_evidence_pending is True
            and self.wave7_authorized is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideGAElitePilotRolloutStrategyReport:
    if not path.exists():
        raise AfriRideGAElitePilotRolloutStrategyValidationError(
            "GA Elite pilot rollout strategy contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: GA ELITE PILOT ROLLOUT STRATEGY CONTRACT")
    _require(text, "CLASSIFICATION: EVIDENCE-GOVERNED EXPANSION PLAN")
    _require(text, "Execution -> Evidence -> Replay -> Verification -> Certification -> Expansion")
    _require(text, "Expansion -> Hope -> Evidence later")
    _require(text, "Field Evidence: PENDING")
    _require(text, "Wave 7: NOT AUTHORIZED")

    payload = _load_payload(text)
    _require_equal(payload["rollout_law"], ROLLOUT_LAW, "rollout law")
    _require_equal(payload["forbidden_law"], FORBIDDEN_LAW, "forbidden law")
    _validate_phases(payload["phases"])
    _validate_gates(payload["gates"])

    report = AfriRideGAElitePilotRolloutStrategyReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        field_evidence_pending=payload["field_evidence_pending"],
        wave7_authorized=payload["wave7_authorized"],
    )
    if not report.verified:
        raise AfriRideGAElitePilotRolloutStrategyValidationError(
            "GA Elite pilot rollout strategy report is not verified"
        )
    return report


def _validate_phases(phases: dict[str, Any]) -> None:
    phase_1 = phases["phase_1"]
    phase_2 = phases["phase_2"]
    phase_3 = phases["phase_3"]
    if phase_1["required_origin"] != "field_observed" or phase_1["min_completed_rides"] != 20:
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 1 gate mismatch")
    if phase_1["replay_verification"] != "100%" or phase_1["authority_violations"] != 0:
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 1 integrity mismatch")
    if phase_2["min_completed_rides"] != 500 or phase_2["replay_success"] != "100%":
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 2 gate mismatch")
    if phase_2["constitutional_violations"] != 0:
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 2 governance mismatch")
    if phase_3["min_completed_rides"] != 10000 or phase_3["replay_admissibility"] != "100%":
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 3 gate mismatch")
    if phase_3["authority_boundary_violations"] != 0:
        raise AfriRideGAElitePilotRolloutStrategyValidationError("phase 3 governance mismatch")


def _validate_gates(gates: dict[str, Any]) -> None:
    expected = {
        "gate_a": ("field_evidence", "pilot_certification", "replay_verification", "evidence_origin_verification"),
        "gate_b": ("multi_driver_proof", "continuity_proof", "entropy_proof", "operational_evidence_report"),
        "gate_c": (
            "economic_sustainability_proof",
            "marketplace_proof",
            "operational_continuity_proof",
            "replay_legitimacy_proof",
            "governance_approval",
        ),
    }
    for gate, requirements in expected.items():
        _require_equal(gates[gate]["requires"], requirements, f"{gate} requirements")


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(ga_elite_pilot_rollout_strategy:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideGAElitePilotRolloutStrategyValidationError(
            "missing ga_elite_pilot_rollout_strategy yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("ga_elite_pilot_rollout_strategy") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideGAElitePilotRolloutStrategyValidationError(
            "invalid ga_elite_pilot_rollout_strategy yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideGAElitePilotRolloutStrategyValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideGAElitePilotRolloutStrategyValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideGAElitePilotRolloutStrategyValidationError as exc:
        print(f"GA ELITE PILOT ROLLOUT STRATEGY REJECTED: {exc}")
        return 1
    print("AfriRide GA Elite pilot rollout strategy validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"field_evidence_pending={report.field_evidence_pending}")
    print(f"wave7_authorized={report.wave7_authorized}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
