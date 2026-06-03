"""Validate the AfriRide field execution transition boundary contract."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_FIELD_EXECUTION_TRANSITION_BOUNDARY.md"

ARCHITECTURAL_CLAIMS = (
    "Execution Grade Pilot System",
    "Evidence Origin Control",
    "Certification Gate",
    "Wave 7 Gate",
    "Pilot Rollout Governance",
    "Pilot Validator Chain",
    "Replay-Governed Promotion Path",
    "CI Enforcement",
    "Constitutional Pipeline Enforcement",
)
AUTHORITY_CHAIN = (
    "adr",
    "invariant",
    "control",
    "execution",
    "evidence",
    "receipt",
    "certification",
)
PROMOTION_FUNCTION = (
    "execute",
    "trace",
    "replay",
    "verify",
    "compress",
    "certify",
    "lock",
    "expand",
)
OPERATIONAL_LEGITIMACY_CHAIN = (
    "field_execution",
    "evidence",
    "replay",
    "verification",
    "certification",
)
WAVE7_FORBIDDEN_UNLOCKS = (
    "code",
    "tests",
    "simulation",
    "ci_success",
    "architecture",
    "documentation",
    "validators",
)
NONDETERMINISM_ENVELOPE = (
    "gps_jitter",
    "network_latency",
    "packet_loss",
    "mobile_os_constraints",
    "human_timing_variability",
)


class AfriRideFieldExecutionTransitionBoundaryValidationError(RuntimeError):
    """Raised when the field execution transition boundary is invalid."""


@dataclass(frozen=True)
class AfriRideFieldExecutionTransitionBoundaryReport:
    schema: str
    status: str
    classification: str
    governance_machine_exists: bool
    operational_evidence_present: bool
    field_execution_performed: bool
    wave7_authorized: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.field_execution_transition_boundary.v1"
            and self.status == "field_execution_transition_boundary_contract"
            and self.classification == "operational_evidence_gate"
            and self.governance_machine_exists is True
            and self.operational_evidence_present is False
            and self.field_execution_performed is False
            and self.wave7_authorized is False
        )


def validate_contract(path: Path = CONTRACT_DOC) -> AfriRideFieldExecutionTransitionBoundaryReport:
    if not path.exists():
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "field execution transition boundary contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: FIELD EXECUTION TRANSITION BOUNDARY CONTRACT")
    _require(text, "CLASSIFICATION: OPERATIONAL EVIDENCE GATE")
    _require(text, "The AfriRide governance machine exists. That is an architectural claim.")
    _require(text, "Operational Evidence: NOT_PRESENT")
    _require(text, "Field Execution: NOT_PERFORMED")
    _require(text, "Wave 7: LOCKED")
    _require(text, "Reality is the only authority that can advance the system.")
    _require(text, "The system is now incapable of advancing itself.")
    _require(text, "Only reality interacting with the system under governance constraints can produce the next state.")
    _require(text, "No other entry point exists.")

    payload = _load_payload(text)
    _require_equal(
        payload["admissible_architectural_claims"],
        ARCHITECTURAL_CLAIMS,
        "architectural claims",
    )
    _require_equal(payload["authority_chain"], AUTHORITY_CHAIN, "authority chain")
    _require_equal(payload["promotion_function"], PROMOTION_FUNCTION, "promotion function")
    _validate_reality_authority(payload)
    _validate_orthogonal_systems(payload["orthogonal_systems"])
    _validate_evidence_boundaries(payload)
    _validate_wave7_boundary(payload)
    _require_equal(
        payload["nondeterminism_envelope"],
        NONDETERMINISM_ENVELOPE,
        "nondeterminism envelope",
    )
    _validate_final_classification(payload["final_classification"])

    report = AfriRideFieldExecutionTransitionBoundaryReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        governance_machine_exists=payload["governance_machine_exists"],
        operational_evidence_present=payload["operational_evidence_present"],
        field_execution_performed=payload["field_execution_performed"],
        wave7_authorized=payload["wave7_authorized"],
    )
    if not report.verified:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "field execution transition boundary report is not verified"
        )
    return report


def _validate_reality_authority(payload: dict[str, Any]) -> None:
    if payload["advancement_authority"] != "reality_only":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "advancement authority must be reality_only"
        )
    if payload["repository_scope"] != "terminal_pre_operational":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "repository scope must be terminal_pre_operational"
        )
    if payload["governance_saturation"] is not True:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "governance saturation must be true"
        )
    if payload["validator_system"] != "SATURATED":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "validator system must be saturated"
        )
    if payload["certification_system"] != "SATURATED":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "certification system must be saturated"
        )
    if payload["additional_governance_hardening_value"] != "diminishing":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "additional governance hardening value must be diminishing"
        )
    if payload["unresolved_uncertainty"] != "external_reality_interaction":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "unresolved uncertainty must be external reality interaction"
        )
    if payload["authority_source_after_boundary"] != "external_reality":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "authority source after boundary must be external reality"
        )
    if payload["repository_outputs_can_produce_operational_legitimacy"] is not False:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "repository outputs must not produce operational legitimacy"
        )
    if payload["system_can_advance_itself"] is not False:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "system must be incapable of advancing itself"
        )
    if payload["next_state_producer"] != "governed_reality_interaction":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "next state producer must be governed reality interaction"
        )
    if payload["operational_legitimacy_entrypoint"] != "field_execution_to_certification":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "operational legitimacy entrypoint mismatch"
        )
    if payload["first_operational_legitimacy_event"] != "first_replay_admissible_field_execution":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "first operational legitimacy event mismatch"
        )
    if payload["alternate_operational_entrypoints_allowed"] is not False:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "alternate operational entrypoints must be forbidden"
        )
    _require_equal(
        payload["operational_legitimacy_chain"],
        OPERATIONAL_LEGITIMACY_CHAIN,
        "operational legitimacy chain",
    )


def _validate_orthogonal_systems(systems: dict[str, Any]) -> None:
    governance = systems["governance_engine"]
    if governance["state"] != "COMPLETE":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "governance engine must be complete"
        )
    _require_equal(
        governance["responsibilities"],
        ("defines_truth", "defines_rules", "defines_promotion", "validates_structure"),
        "governance engine responsibilities",
    )

    reality = systems["reality_interface"]
    if reality["state"] != "NOT_YET_ACTIVATED":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "reality interface must remain not yet activated"
        )
    _require_equal(
        reality["responsibilities"],
        ("executes_in_field", "produces_evidence", "feeds_replay_system"),
        "reality interface responsibilities",
    )
    _require_equal(
        systems["boundary_properties"],
        ("unskippable", "unfakeable", "uncompressible"),
        "boundary properties",
    )


def _validate_evidence_boundaries(payload: dict[str, Any]) -> None:
    synthetic = payload["synthetic_evidence"]
    if synthetic["may_validate"] is not True or synthetic["may_stress"] is not True:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "synthetic evidence validation permissions mismatch"
        )
    if synthetic["may_certify"] is not False:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "synthetic evidence must not certify"
        )
    if synthetic["may_authorize_wave7"] is not False:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "synthetic evidence must not authorize Wave 7"
        )

    field = payload["field_evidence"]
    if field["may_validate"] is not True or field["may_certify"] is not True:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "field evidence certification permissions mismatch"
        )
    if field["may_authorize_wave7_if_all_other_gates_pass"] is not True:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "field evidence must be eligible for Wave 7 only after all gates pass"
        )


def _validate_wave7_boundary(payload: dict[str, Any]) -> None:
    _require_equal(
        payload["wave7_unlock_forbidden_by"],
        WAVE7_FORBIDDEN_UNLOCKS,
        "Wave 7 forbidden unlocks",
    )
    _require_equal(
        payload["wave7_unlock_requires"],
        ("certified_operational_evidence",),
        "Wave 7 unlock requirements",
    )
    if payload["next_legitimacy_artifact"] != "Field Execution Record":
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "next legitimacy artifact must be Field Execution Record"
        )
    _require_equal(
        payload["field_record_must_pass"],
        (
            "execute_real_environment",
            "trace_captured",
            "replay_deterministic_reproduction",
            "verify_validator_pass",
            "certify_gate_approval",
        ),
        "field record requirements",
    )
    _require_equal(
        payload["required_transformation"],
        (
            "nondeterministic_environment",
            "deterministic_interpretation",
            "replay_convergence",
        ),
        "field transformation requirements",
    )
    _require_equal(
        payload["pilot_success_requires"],
        (
            "all_trips_fully_traced",
            "all_trips_fully_replayable",
            "all_trips_replay_equivalent",
            "all_trips_validator_passing",
            "all_trips_certification_admissible",
        ),
        "pilot success requirements",
    )


def _validate_final_classification(classification: dict[str, str]) -> None:
    expected = {
        "governance_layer": "COMPLETE",
        "execution_layer": "DEFINED",
        "validation_layer": "COMPLETE",
        "certification_layer": "COMPLETE",
        "evidence_governance": "COMPLETE",
        "operational_evidence": "NOT_PRESENT",
        "field_execution": "NOT_PERFORMED",
        "replay_under_real_conditions": "UNPROVEN",
        "operational_certification": "NOT_ADMISSIBLE",
        "wave7": "LOCKED",
        "repository_scope": "TERMINAL_PRE_OPERATIONAL",
        "authority_source": "EXTERNAL_REALITY",
    }
    if classification != expected:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "final classification mismatch"
        )


def _load_payload(text: str) -> dict[str, Any]:
    match = re.search(
        r"```yaml\n(field_execution_transition_boundary:.*?)\n```",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "missing field_execution_transition_boundary yaml block"
        )
    data = yaml.safe_load(match.group(1))
    payload = data.get("field_execution_transition_boundary") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            "invalid field_execution_transition_boundary yaml block"
        )
    return payload


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            f"missing phrase: {phrase}"
        )


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideFieldExecutionTransitionBoundaryValidationError(
            f"{label} mismatch"
        )


def main() -> int:
    try:
        report = validate_contract()
    except AfriRideFieldExecutionTransitionBoundaryValidationError as exc:
        print(f"FIELD EXECUTION TRANSITION BOUNDARY REJECTED: {exc}")
        return 1
    print("AfriRide field execution transition boundary validation PASSED")
    print(f"schema={report.schema}")
    print(f"status={report.status}")
    print(f"classification={report.classification}")
    print(f"governance_machine_exists={report.governance_machine_exists}")
    print(f"operational_evidence_present={report.operational_evidence_present}")
    print(f"field_execution_performed={report.field_execution_performed}")
    print(f"wave7_authorized={report.wave7_authorized}")
    print(f"verified={report.verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
