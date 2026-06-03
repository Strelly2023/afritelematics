"""Validate the AfriRide execution-grade pilot system contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_EXECUTION_GRADE_PILOT_SYSTEM.md"

TRUTH_CHAIN = (
    "adr",
    "invariant",
    "binding",
    "rule",
    "guard",
    "runtime",
    "trace",
    "replay",
    "evidence",
    "certification",
)
EXECUTION_FORMULA = (
    "execute",
    "trace",
    "replay",
    "verify",
    "compress",
    "certify",
    "lock",
    "expand",
)
FORBIDDEN_FORMULA = ("launch", "grow", "break", "patch", "repeat")


class AfriRideExecutionGradePilotSystemValidationError(RuntimeError):
    """Raised when the execution-grade pilot system contract is invalid."""


@dataclass(frozen=True)
class AfriRideExecutionGradePilotSystemReport:
    schema: str
    status: str
    classification: str
    wave6_framework_complete: bool
    field_evidence_pending: bool
    wave7_authorized: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.execution_grade_pilot_system.v1"
            and self.status == "execution_grade_pilot_system_contract"
            and self.classification == "constitutional_replay_governed_expansion_system"
            and self.wave6_framework_complete is True
            and self.field_evidence_pending is True
            and self.wave7_authorized is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideExecutionGradePilotSystemReport:
    if not path.exists():
        raise AfriRideExecutionGradePilotSystemValidationError(
            "execution-grade pilot system contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: EXECUTION-GRADE PILOT SYSTEM CONTRACT")
    _require(text, "CLASSIFICATION: CONSTITUTIONAL REPLAY-GOVERNED EXPANSION SYSTEM")
    _require(text, "ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> RUNTIME -> TRACE -> REPLAY -> EVIDENCE -> CERTIFICATION")
    _require(text, "Execute -> Trace -> Replay -> Verify -> Compress -> Certify -> Lock -> Expand")
    _require(text, "Launch -> Grow -> Break -> Patch -> Repeat")
    _require(text, "Wave 7 = REJECTED")

    payload = _load_payload(text)
    _require_equal(payload["truth_chain"], TRUTH_CHAIN, "truth chain")
    _require_equal(payload["execution_formula"], EXECUTION_FORMULA, "execution formula")
    _require_equal(payload["forbidden_formula"], FORBIDDEN_FORMULA, "forbidden formula")
    _validate_governance_model(payload["governance_model"])
    _validate_runtime_guards(payload["runtime_guards"])
    _validate_evidence_system(payload["evidence_system"])
    _validate_compression_layer(payload["compression_layer"])
    _validate_certification_system(payload["certification_system"])
    _validate_failure_classes(payload["failure_classes"])
    _validate_wave_gates(payload["wave_gates"])

    report = AfriRideExecutionGradePilotSystemReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        wave6_framework_complete=payload["wave6_framework_complete"],
        field_evidence_pending=payload["field_evidence_pending"],
        wave7_authorized=payload["wave7_authorized"],
    )
    if not report.verified:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "execution-grade pilot system report is not verified"
        )
    return report


def _validate_governance_model(model: dict[str, Any]) -> None:
    expected_counts = {
        "phase_1": (3, 5),
        "phase_2": (3, 4),
        "phase_3": (3, 4),
    }
    for phase, (adr_count, invariant_count) in expected_counts.items():
        data = model[phase]
        if len(data["adrs"]) != adr_count:
            raise AfriRideExecutionGradePilotSystemValidationError(f"{phase} ADR count mismatch")
        if len(data["invariants"]) != invariant_count:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{phase} invariant count mismatch"
            )
    if "INVARIANT-REPLAY-EQUIVALENCE" not in model["phase_1"]["invariants"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 1 must include replay equivalence"
        )
    if "INVARIANT-ENTROPY-RESILIENCE" not in model["phase_2"]["invariants"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 2 must include entropy resilience"
        )
    if "INVARIANT-LEDGER-BALANCE" not in model["phase_3"]["invariants"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 3 must include ledger balance"
        )


def _validate_runtime_guards(guards: dict[str, Any]) -> None:
    ride_guard = guards["ride_state_guard"]
    if ride_guard["valid_sequence"] != [
        "REQUESTED",
        "ASSIGNED",
        "ACCEPTED",
        "STARTED",
        "COMPLETED",
    ]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "ride lifecycle guard sequence mismatch"
        )
    if ride_guard["invalid_sequence"] != ["REQUESTED", "COMPLETED"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "ride lifecycle invalid transition mismatch"
        )
    replay_guard = guards["replay_consistency_guard"]
    if replay_guard["check"] != "execution_hash_equals_replay_hash":
        raise AfriRideExecutionGradePilotSystemValidationError("replay guard mismatch")
    evidence_guard = guards["evidence_origin_guard"]
    if evidence_guard["synthetic_may_certify"] is not False:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "synthetic evidence must not certify"
        )
    if evidence_guard["field_observed_certification_eligible"] is not True:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "field observed evidence must be certification eligible"
        )
    if guards["fare_calculation_guard"]["same_inputs_same_fare"] is not True:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "fare guard must enforce deterministic fare calculation"
        )


def _validate_evidence_system(evidence: dict[str, Any]) -> None:
    expected_paths = {
        "phase_1": "traces/pilot_runs/day_one_001/",
        "phase_2": "traces/pilot_runs/operational_pilot/",
        "phase_3": "traces/pilot_runs/production_pilot/",
    }
    for phase, expected_path in expected_paths.items():
        if evidence[phase]["path"] != expected_path:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{phase} evidence path mismatch"
            )
        if not evidence[phase]["required"]:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{phase} evidence requirements missing"
            )
    if "replay_verification_result.json" not in evidence["phase_1"]["required"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 1 evidence must include replay verification"
        )
    if "replay_reports/" not in evidence["phase_2"]["required"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 2 evidence must include replay reports"
        )
    if "replay_verification/" not in evidence["phase_3"]["required"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 3 evidence must include replay verification"
        )


def _validate_compression_layer(compression: dict[str, Any]) -> None:
    expected_paths = {
        "phase_1": "certification/phase1_bundle/",
        "phase_2": "certification/phase2_bundle/",
        "phase_3": "certification/phase3_bundle/",
    }
    for phase, expected_path in expected_paths.items():
        if compression[phase]["path"] != expected_path:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{phase} compression path mismatch"
            )
        if not compression[phase]["outputs"]:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{phase} compression outputs missing"
            )
    if "replay_truth_proof.json" not in compression["phase_1"]["outputs"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 1 compression must include replay truth proof"
        )
    if "entropy_resilience_proof.json" not in compression["phase_2"]["outputs"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 2 compression must include entropy resilience proof"
        )
    if "replay_authority_report.json" not in compression["phase_3"]["outputs"]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "phase 3 compression must include replay authority report"
        )


def _validate_certification_system(certification: dict[str, Any]) -> None:
    if certification["validator"] != "certification_validator.py":
        raise AfriRideExecutionGradePilotSystemValidationError(
            "certification validator mismatch"
        )
    required = (
        "all_invariants_pass",
        "all_guards_pass",
        "all_evidence_exists",
        "replay_verified",
        "no_governance_violations",
    )
    _require_equal(certification["requires"], required, "certification requirements")
    if certification["produces"] != "phase_certificate.json":
        raise AfriRideExecutionGradePilotSystemValidationError(
            "certification output mismatch"
        )
    if certification["locks"] != [
        "BIND-PHASE-1-LOCK.yaml",
        "BIND-PHASE-2-LOCK.yaml",
        "BIND-PHASE-3-LOCK.yaml",
    ]:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "certification locks mismatch"
        )


def _validate_failure_classes(failures: dict[str, Any]) -> None:
    expected = {
        "class_a": ("Replay Divergence", ("Stop Pilot", "Open Incident", "Replay Audit")),
        "class_b": ("Evidence Corruption", ("Reject Certification", "Freeze Bundle", "Root Cause Analysis")),
        "class_c": ("Invariant Violation", ("Stop Expansion", "Freeze Current Phase", "Remediate")),
        "class_d": ("Economic Inconsistency", ("Freeze Marketplace", "Audit Ledger", "Governance Review")),
    }
    for class_id, (failure_type, actions) in expected.items():
        if failures[class_id]["type"] != failure_type:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"{class_id} failure type mismatch"
            )
        _require_equal(failures[class_id]["action"], actions, f"{class_id} actions")


def _validate_wave_gates(gates: dict[str, Any]) -> None:
    wave6 = gates["wave6"]
    for key in (
        "framework_complete",
        "evidence_origin_control_implemented",
        "certification_protected",
        "pilot_ready",
    ):
        if wave6[key] is not True:
            raise AfriRideExecutionGradePilotSystemValidationError(
                f"wave6 {key} must be true"
            )
    wave7 = gates["wave7"]
    if wave7["authorized"] is not False:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "wave7 must remain unauthorized"
        )
    expected = (
        "Phase 1 Certificate",
        "Phase 2 Certificate",
        "Phase 3 Certificate",
        "Replay Proof",
        "Operational Evidence",
        "Governance Approval",
    )
    _require_equal(wave7["rejected_without"], expected, "wave7 rejection requirements")


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(execution_grade_pilot_system:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideExecutionGradePilotSystemValidationError(
            "missing execution_grade_pilot_system yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("execution_grade_pilot_system") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideExecutionGradePilotSystemValidationError(
            "invalid execution_grade_pilot_system yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideExecutionGradePilotSystemValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideExecutionGradePilotSystemValidationError(f"{label} mismatch")


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideExecutionGradePilotSystemValidationError as exc:
        print(f"EXECUTION-GRADE PILOT SYSTEM REJECTED: {exc}")
        return 1
    print("AfriRide execution-grade pilot system validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"wave6_framework_complete={report.wave6_framework_complete}")
    print(f"field_evidence_pending={report.field_evidence_pending}")
    print(f"wave7_authorized={report.wave7_authorized}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
