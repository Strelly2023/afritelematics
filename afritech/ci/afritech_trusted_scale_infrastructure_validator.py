"""Validate trusted-scale infrastructure doctrine and pilot verification docs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]

ADR_0042 = ROOT / "afritech/governance/adr/ADR-0042-field-evidence-collection.yaml"
ADR_0043 = ROOT / "afritech/governance/adr/ADR-0043-simulation-reality-reconciliation-layer.yaml"
RULE_062 = ROOT / "afritech/governance/rules/RULE-062-field-evidence-collection.yaml"
RULE_063 = ROOT / "afritech/governance/rules/RULE-063-simulation-reality-reconciliation.yaml"
BIND_040 = ROOT / "afritech/governance/bindings/BIND-040-field-evidence-collection.yaml"
BIND_041 = ROOT / "afritech/governance/bindings/BIND-041-simulation-reality-reconciliation.yaml"
FIELD_EVIDENCE_DOC = ROOT / "docs/architecture/AFRIFIELD_EVIDENCE_COLLECTION.md"
RECONCILIATION_DOC = ROOT / "docs/architecture/AFRISIMULATION_REALITY_RECONCILIATION.md"
SCENARIO_DOC = ROOT / "docs/operations/AFRITECH_FIRST_LIVE_DEPLOYMENT_SCENARIO.md"
RUNBOOK = ROOT / "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md"
OPERATING_MODEL = ROOT / "docs/architecture/AFRITECH_OPERATING_MODEL.md"

AUTHORITY_CHAIN = (
    "Constitution",
    "Deterministic Truth",
    "Replay",
    "Proof",
)

REQUIRED_ADR_KEYS = (
    "id",
    "title",
    "status",
    "decision",
    "context",
    "authority_model",
    "reality_interface",
    "trust_at_scale_controls",
    "forbidden",
    "consequences",
    "verification",
    "rules",
    "bindings",
)

REQUIRED_REALITY_INTERFACE = {
    "role": "external_observation_ingress",
    "authoritative": False,
    "mutates_dispatch": False,
    "mutates_replay": False,
    "mutates_proof": False,
    "mutates_settlement": False,
}

REQUIRED_BINDINGS = {
    "dispatch_id",
    "operation_id",
    "selected_participant_id",
    "event_sequence_id",
    "evidence_hash",
    "captured_at",
}

REQUIRED_FORBIDDEN = {
    "field_evidence_as_truth_authority",
    "field_evidence_overrides_replay",
    "field_evidence_overrides_dispatch",
    "field_evidence_overrides_settlement",
    "field_evidence_mutates_state",
}

REQUIRED_TRUST_CONTROLS = {
    "deterministic serialization",
    "stable hashing",
    "replay validation",
    "dispatch participant binding",
    "operation identity binding",
    "ordered event sequence validation",
    "read-only export",
    "invariant report generation",
    "pilot verification runbook execution",
}

REQUIRED_DOC_TEXT = (
    "Status: ACCEPTED REALITY INTERFACE",
    "Classification: NON-AUTHORITATIVE FIELD EVIDENCE INGESTION SURFACE",
    "Field evidence is deliberately outside the authority chain.",
    "Constitution defines authority.",
    "Deterministic Truth defines truth.",
    "Replay validates truth.",
    "Proof demonstrates truth.",
    "field evidence does not define truth, proof, replay, dispatch, or settlement",
    "field evidence cannot override a dispatch-selected participant",
    "afritech/ci/afritech_field_evidence_runtime_validator.py",
    "full-system pilot verification runbook execution",
)

REQUIRED_RUNBOOK_TEXT = (
    "Status: PILOT DEPLOYMENT VERIFICATION RUNBOOK",
    "Classification: CONSTITUTIONALLY ENFORCED TRUST-AT-SCALE OPERATIONS SURFACE",
    "ADR-0042 Field Evidence Collection",
    "Constitution defines authority.",
    "Deterministic Truth defines truth.",
    "Replay validates truth.",
    "Proof demonstrates truth.",
    "Phase 0. Scope Lock",
    "Phase 1. Constitutional And Doctrine Verification",
    "Phase 2. Reality Interface Verification",
    "afritech.ci.afritech_field_evidence_runtime_validator",
    "Phase 3. Replay, Proof, And Evidence Verification",
    "Phase 4. Pilot Deployment Verification",
    "Phase 5. Full Constitutional Pipeline Registry Check",
    "Phase 6. Field Operation Evidence Collection",
    "Phase 7. Operator Review",
    "Phase 8. Pilot Closeout",
    "Phase 9. Simulation Reality Reconciliation",
    "Phase 10. Operator Decision Protocol",
    "Stop Conditions",
    "afritech_eight_pillars_validator",
    "python -m afritech.ci.afritech_field_evidence_runtime_validator",
    "python -m afritech.ci.afritech_pilot_dataset_simulation_validator",
    "afritech/tests/mobility/test_field_evidence.py",
    "field evidence is bounded",
)


class AfriTechTrustedScaleInfrastructureError(RuntimeError):
    """Raised when trusted-scale infrastructure doctrine is incomplete."""


@dataclass(frozen=True)
class AfriTechTrustedScaleInfrastructureReport:
    authority_chain: tuple[str, ...]
    adr_id: str
    rule_id: str
    binding_id: str
    runbook: str
    required_bindings: tuple[str, ...]
    forbidden: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.authority_chain == AUTHORITY_CHAIN
            and self.adr_id == "ADR-0042"
            and self.rule_id == "RULE-062"
            and self.binding_id == "BIND-040"
            and set(self.required_bindings) == REQUIRED_BINDINGS
            and set(self.forbidden) == REQUIRED_FORBIDDEN
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.trusted_scale_infrastructure_report.v1",
            "authority_chain": self.authority_chain,
            "adr_id": self.adr_id,
            "rule_id": self.rule_id,
            "binding_id": self.binding_id,
            "runbook": self.runbook,
            "required_bindings": self.required_bindings,
            "forbidden": self.forbidden,
            "verified": self.verified,
        }


def validate() -> AfriTechTrustedScaleInfrastructureReport:
    adr = _load_yaml(ADR_0042)
    adr_reconciliation = _load_yaml(ADR_0043)
    rule = _load_yaml(RULE_062)
    rule_reconciliation = _load_yaml(RULE_063)
    binding = _load_yaml(BIND_040)
    binding_reconciliation = _load_yaml(BIND_041)

    _validate_adr(adr)
    _validate_reconciliation_adr(adr_reconciliation)
    _validate_rule(rule)
    _validate_reconciliation_rule(rule_reconciliation)
    _validate_binding(binding)
    _validate_reconciliation_binding(binding_reconciliation)
    _validate_doc(FIELD_EVIDENCE_DOC, REQUIRED_DOC_TEXT)
    _validate_doc(
        RECONCILIATION_DOC,
        (
            "Status: ACCEPTED RECONCILIATION BOUNDARY",
            "Classification: NON-AUTHORITATIVE OPERATIONAL FEEDBACK SURFACE",
            "Simulation and reality are compared under this chain. Neither becomes authority.",
        ),
    )
    _validate_doc(
        SCENARIO_DOC,
        (
            "Status: FIRST LIVE OPERATION SCENARIO",
            "Classification: GOVERNED AIRPORT PILOT DEPLOYMENT SURFACE",
            "Scenario ID: airport-zone-001",
        ),
    )
    _validate_doc(RUNBOOK, REQUIRED_RUNBOOK_TEXT)
    _validate_doc(OPERATING_MODEL, ("Constitution defines authority.", "Products consume governed capability."))

    report = AfriTechTrustedScaleInfrastructureReport(
        authority_chain=tuple(adr["authority_model"]["chain"]),
        adr_id=str(adr["id"]),
        rule_id=str(rule["id"]),
        binding_id=str(binding["id"]),
        runbook=str(adr["verification"]["runbook"]),
        required_bindings=tuple(adr["reality_interface"]["required_bindings"]),
        forbidden=tuple(adr["forbidden"]),
    )
    if not report.verified:
        raise AfriTechTrustedScaleInfrastructureError(
            "trusted-scale infrastructure report failed"
        )
    return report


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AfriTechTrustedScaleInfrastructureError(
            f"missing required file: {path.relative_to(ROOT)}"
        )
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AfriTechTrustedScaleInfrastructureError(
            f"YAML root must be a mapping: {path.relative_to(ROOT)}"
        )
    return payload


def _validate_adr(adr: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_ADR_KEYS if key not in adr]
    if missing:
        raise AfriTechTrustedScaleInfrastructureError(
            f"ADR-0042 missing keys: {missing}"
        )
    if adr["id"] != "ADR-0042":
        raise AfriTechTrustedScaleInfrastructureError("ADR id mismatch")
    if adr["status"] != "accepted":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0042 must be accepted")
    if adr["title"] != "Field Evidence Collection Reality Interface":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0042 title mismatch")

    authority_model = adr["authority_model"]
    if not isinstance(authority_model, dict):
        raise AfriTechTrustedScaleInfrastructureError("authority_model missing")
    if tuple(authority_model.get("chain", ())) != AUTHORITY_CHAIN:
        raise AfriTechTrustedScaleInfrastructureError("authority chain mismatch")
    principle = str(authority_model.get("principle", ""))
    for phrase in (
        "Constitution defines authority.",
        "Deterministic Truth defines truth.",
        "Replay validates truth.",
        "Proof demonstrates truth.",
        "does not become part of the authority chain",
    ):
        if phrase not in principle:
            raise AfriTechTrustedScaleInfrastructureError(
                f"authority principle missing phrase: {phrase}"
            )

    interface = adr["reality_interface"]
    if not isinstance(interface, dict):
        raise AfriTechTrustedScaleInfrastructureError("reality_interface missing")
    for key, expected in REQUIRED_REALITY_INTERFACE.items():
        if interface.get(key) is not expected and interface.get(key) != expected:
            raise AfriTechTrustedScaleInfrastructureError(
                f"reality_interface {key} mismatch"
            )
    if set(interface.get("required_bindings", ())) != REQUIRED_BINDINGS:
        raise AfriTechTrustedScaleInfrastructureError(
            "reality_interface required bindings mismatch"
        )

    if set(adr["trust_at_scale_controls"]) != REQUIRED_TRUST_CONTROLS:
        raise AfriTechTrustedScaleInfrastructureError(
            "trust-at-scale controls mismatch"
        )
    if set(adr["forbidden"]) != REQUIRED_FORBIDDEN:
        raise AfriTechTrustedScaleInfrastructureError("forbidden list mismatch")
    if adr["verification"]["runbook"] != "docs/operations/AFRITECH_FULL_SYSTEM_VERIFICATION_RUNBOOK.md":
        raise AfriTechTrustedScaleInfrastructureError("runbook binding mismatch")
    if adr["verification"].get("runtime_validator") != "afritech.ci.afritech_field_evidence_runtime_validator":
        raise AfriTechTrustedScaleInfrastructureError("runtime validator binding mismatch")
    if "RULE-062-field-evidence-collection.yaml" not in adr["rules"]:
        raise AfriTechTrustedScaleInfrastructureError("RULE-062 missing from ADR")
    if "BIND-040-field-evidence-collection.yaml" not in adr["bindings"]:
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 missing from ADR")


def _validate_rule(rule: dict[str, Any]) -> None:
    if rule.get("id") != "RULE-062":
        raise AfriTechTrustedScaleInfrastructureError("RULE-062 id mismatch")
    forbidden = set(rule.get("forbidden", ()))
    if not REQUIRED_FORBIDDEN <= forbidden:
        raise AfriTechTrustedScaleInfrastructureError(
            "RULE-062 forbidden list does not cover ADR-0042"
        )
    ci_entries = set(rule.get("ci", ()))
    if "afritech/ci/afritech_field_evidence_runtime_validator.py" not in ci_entries:
        raise AfriTechTrustedScaleInfrastructureError("RULE-062 runtime validator missing")
    if "afritech/tests/mobility/test_field_evidence.py" not in ci_entries:
        raise AfriTechTrustedScaleInfrastructureError("RULE-062 CI test missing")


def _validate_reconciliation_adr(adr: dict[str, Any]) -> None:
    if adr.get("id") != "ADR-0043":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 id mismatch")
    if adr.get("status") != "accepted":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 must be accepted")
    if adr.get("title") != "Simulation Reality Reconciliation Layer":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 title mismatch")
    authority_model = adr.get("authority_model")
    if not isinstance(authority_model, dict):
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 authority_model missing")
    if tuple(authority_model.get("chain", ())) != AUTHORITY_CHAIN:
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 authority chain mismatch")
    principle = str(authority_model.get("principle", ""))
    for phrase in (
        "Constitution defines authority.",
        "Deterministic Truth defines truth.",
        "Replay validates truth.",
        "Proof demonstrates truth.",
    ):
        if phrase not in principle:
            raise AfriTechTrustedScaleInfrastructureError(
                f"ADR-0043 authority principle missing phrase: {phrase}"
            )
    reconciliation_layer = adr.get("reconciliation_layer")
    if not isinstance(reconciliation_layer, dict):
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 reconciliation_layer missing")
    if reconciliation_layer.get("authoritative") is not False:
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 reconciliation layer must be non-authoritative")
    if reconciliation_layer.get("role") != "simulation_vs_reality_comparison":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 reconciliation role mismatch")
    if set(reconciliation_layer.get("required_inputs", ())) != {
        "simulation_dataset_hash",
        "simulation_operation_hashes",
        "live_ingestion_hashes",
        "live_collection_hashes",
        "live_proof_hashes",
        "scenario_id",
        "operation_ids",
    }:
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 required inputs mismatch")
    if set(reconciliation_layer.get("required_outputs", ())) != {
        "reconciliation_report",
        "divergence_score",
        "calibrated_adjustment_notes",
        "stop_or_continue_recommendation",
        "operator_review_trace",
    }:
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 required outputs mismatch")
    if "RULE-063-simulation-reality-reconciliation.yaml" not in adr.get("rules", ()):
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 missing RULE-063")
    if "BIND-041-simulation-reality-reconciliation.yaml" not in adr.get("bindings", ()):
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 missing BIND-041")
    if adr.get("verification", {}).get("validator") != "afritech.ci.afritech_reconciliation_validator":
        raise AfriTechTrustedScaleInfrastructureError("ADR-0043 validator binding mismatch")


def _validate_binding(binding: dict[str, Any]) -> None:
    if binding.get("id") != "BIND-040":
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 id mismatch")
    if "ADR-0042" not in binding.get("linked_adr", ()):
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 missing ADR-0042")
    if "RULE-062" not in binding.get("linked_rules", ()):
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 missing RULE-062")
    bindings = binding.get("bindings")
    if not isinstance(bindings, list) or len(bindings) < 2:
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 bindings incomplete")
    for item in bindings:
        if not isinstance(item, dict):
            raise AfriTechTrustedScaleInfrastructureError("BIND-040 binding invalid")
        if item.get("runtime_authoritative") is not False:
            raise AfriTechTrustedScaleInfrastructureError(
                f"BIND-040 binding must be non-authoritative: {item.get('id')}"
            )
    validators = set((binding.get("ci") or {}).get("validators", ()))
    if "afritech.ci.afritech_field_evidence_runtime_validator" not in validators:
        raise AfriTechTrustedScaleInfrastructureError("BIND-040 runtime validator missing")


def _validate_reconciliation_rule(rule: dict[str, Any]) -> None:
    if rule.get("id") != "RULE-063":
        raise AfriTechTrustedScaleInfrastructureError("RULE-063 id mismatch")
    forbidden = set(rule.get("forbidden", ()))
    required = {
        "simulation_as_truth_authority",
        "reality_as_truth_authority",
        "reconciliation_as_truth_authority",
        "reconciliation_overrides_dispatch",
        "reconciliation_overrides_proof",
        "reconciliation_mutates_state",
    }
    if not required <= forbidden:
        raise AfriTechTrustedScaleInfrastructureError("RULE-063 forbidden list incomplete")
    ci_entries = set(rule.get("ci", ()))
    if "afritech/ci/afritech_reconciliation_validator.py" not in ci_entries:
        raise AfriTechTrustedScaleInfrastructureError("RULE-063 validator missing")
    if "afritech/tests/mobility/test_reconciliation.py" not in ci_entries:
        raise AfriTechTrustedScaleInfrastructureError("RULE-063 test missing")


def _validate_reconciliation_binding(binding: dict[str, Any]) -> None:
    if binding.get("id") != "BIND-041":
        raise AfriTechTrustedScaleInfrastructureError("BIND-041 id mismatch")
    if "ADR-0043" not in binding.get("linked_adr", ()):
        raise AfriTechTrustedScaleInfrastructureError("BIND-041 missing ADR-0043")
    if "RULE-063" not in binding.get("linked_rules", ()):
        raise AfriTechTrustedScaleInfrastructureError("BIND-041 missing RULE-063")
    bindings = binding.get("bindings")
    if not isinstance(bindings, list) or len(bindings) < 2:
        raise AfriTechTrustedScaleInfrastructureError("BIND-041 bindings incomplete")
    for item in bindings:
        if not isinstance(item, dict):
            raise AfriTechTrustedScaleInfrastructureError("BIND-041 binding invalid")
        if item.get("runtime_authoritative") is not False:
            raise AfriTechTrustedScaleInfrastructureError(
                f"BIND-041 binding must be non-authoritative: {item.get('id')}"
            )
    validators = set((binding.get("ci") or {}).get("validators", ()))
    if "afritech.ci.afritech_reconciliation_validator" not in validators:
        raise AfriTechTrustedScaleInfrastructureError("BIND-041 runtime validator missing")


def _validate_doc(path: Path, required_text: tuple[str, ...]) -> None:
    if not path.exists():
        raise AfriTechTrustedScaleInfrastructureError(
            f"missing required doc: {path.relative_to(ROOT)}"
        )
    text = path.read_text(encoding="utf-8")
    for needle in required_text:
        if needle not in text:
            raise AfriTechTrustedScaleInfrastructureError(
                f"{path.relative_to(ROOT)} missing required text: {needle}"
            )


def format_summary(report: AfriTechTrustedScaleInfrastructureReport) -> str:
    return "\n".join(
        (
            "AfriTech trusted-scale infrastructure validation PASSED",
            "authority_chain=" + " -> ".join(report.authority_chain),
            f"adr={report.adr_id} rule={report.rule_id} binding={report.binding_id}",
            f"runbook={report.runbook}",
            f"required_bindings={len(report.required_bindings)} forbidden={len(report.forbidden)}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriTechTrustedScaleInfrastructureError as exc:
        print(f"AfriTech trusted-scale infrastructure validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
