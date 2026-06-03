"""Validate the AfriRide GA eLive workflow contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DOC = ROOT / "docs/proof/AFRIRIDE_GA_ELIVE_WORKFLOW.md"

REQUIRED_PIPELINE = (
    "rider_request",
    "edge_adapter",
    "normalization",
    "queue_ingestion",
    "partition_routing",
    "worker_execution",
    "core_matching_engine",
    "immutable_event_log",
    "replay_proof",
    "portable_receipt",
    "rider_driver_notification",
    "trip_lifecycle",
    "payment_event",
    "rating_event",
    "constitutional_receipt",
)

PROVEN_PHASE5_EVIDENCE = (
    "driver_app_isolated_validation",
    "driver_backend_contract",
    "rider_backend_contract",
    "sha256_ledger_validation",
    "identity_bound_signatures",
    "portable_ledger_receipts",
    "rider_proof_visibility",
    "driver_proof_visibility",
    "adversarial_fail_closed_integration",
    "live_local_rider_driver_e2e",
    "running_backend_rider_driver_e2e",
)

NOT_YET_PROVEN = (
    "real_flutter_driver_app_to_running_backend_to_real_rider_app",
    "multi_driver_contention",
    "concurrent_ride_execution",
    "network_interruption_recovery",
    "cross_device_signed_event_emission",
    "pilot_field_operation",
    "external_audit_anchoring",
    "production_key_custody",
)

REQUIRED_MODULE_KEYS = (
    "api_entry",
    "adapter",
    "normalization",
    "edge_guard",
    "queue_ingestion",
    "partition_router",
    "worker_pool",
    "core_engine",
    "matching_engine",
    "event_log",
    "event_schema",
    "replay_engine",
    "constitutional_receipt",
    "witness_system",
    "ci_enforcement",
)

FORBIDDEN_CLAIMS = (
    "public launch readiness achieved",
    "field pilot complete",
    "global dispatch fairness proven",
    "byzantine network resilience proven",
    "jurisdiction-grade non-repudiation proven",
)


class AfriRideGAeLiveWorkflowValidationError(RuntimeError):
    """Raised when the GA eLive workflow contract is not admissible."""


@dataclass(frozen=True)
class AfriRideGAeLiveWorkflowReport:
    schema: str
    status: str
    classification: str
    pipeline: tuple[str, ...]
    proven_evidence: tuple[str, ...]
    not_yet_proven: tuple[str, ...]
    truth_authority: str

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.ga_elive_workflow.v1"
            and self.status == "phase_5_active"
            and self.classification == "ga_elive_deterministic_mobility_workflow"
            and self.pipeline == REQUIRED_PIPELINE
            and self.proven_evidence == PROVEN_PHASE5_EVIDENCE
            and self.not_yet_proven == NOT_YET_PROVEN
            and self.truth_authority == "replay_only"
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "status": self.status,
            "classification": self.classification,
            "pipeline": list(self.pipeline),
            "proven_evidence": list(self.proven_evidence),
            "not_yet_proven": list(self.not_yet_proven),
            "truth_authority": self.truth_authority,
            "verified": self.verified,
        }


def validate(path: Path = WORKFLOW_DOC) -> AfriRideGAeLiveWorkflowReport:
    if not path.exists():
        raise AfriRideGAeLiveWorkflowValidationError("GA eLive workflow document missing")

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: PHASE 5 ACTIVE WORKFLOW CONTRACT")
    _require(text, "CLASSIFICATION: GA ELIVE DETERMINISTIC MOBILITY WORKFLOW")
    _require(text, "WORKFLOW CAPABILITY MAY INCREASE; CLIENT AND PRODUCT SURFACES MAY NOT DEFINE TRUTH")
    _require(text, "same declared matching input -> same driver assignment")
    _require(text, "Receipts and UI summaries are derived evidence only.")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideGAeLiveWorkflowValidationError(f"forbidden claim: {phrase}")

    payload = _load_workflow_payload(text)

    if payload["required_pipeline"] != list(REQUIRED_PIPELINE):
        raise AfriRideGAeLiveWorkflowValidationError("required pipeline mismatch")
    if payload["proven_phase5_evidence"] != list(PROVEN_PHASE5_EVIDENCE):
        raise AfriRideGAeLiveWorkflowValidationError("proven evidence mismatch")
    if payload["not_yet_proven"] != list(NOT_YET_PROVEN):
        raise AfriRideGAeLiveWorkflowValidationError("not-yet-proven boundary mismatch")

    rules = payload["execution_rules"]
    for required_true in (
        "no_direct_api_to_core_execution",
        "deterministic_matching_required",
        "race_based_matching_forbidden",
        "event_log_is_append_only",
        "replay_defines_truth",
        "receipts_are_derived_evidence",
    ):
        if rules.get(required_true) is not True:
            raise AfriRideGAeLiveWorkflowValidationError(f"execution rule not enforced: {required_true}")
    for required_false in ("client_truth_authority", "ui_mutation_authority"):
        if rules.get(required_false) is not False:
            raise AfriRideGAeLiveWorkflowValidationError(f"authority boundary not enforced: {required_false}")

    modules = payload["core_modules"]
    for key in REQUIRED_MODULE_KEYS:
        if key not in modules or not modules[key]:
            raise AfriRideGAeLiveWorkflowValidationError(f"missing core module mapping: {key}")

    if payload["write_enabled"] is not False or payload["mutation_authority"] is not False:
        raise AfriRideGAeLiveWorkflowValidationError("workflow contract grants mutation authority")
    if payload["truth_authority"] != "replay_only":
        raise AfriRideGAeLiveWorkflowValidationError("truth authority must remain replay_only")

    report = AfriRideGAeLiveWorkflowReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        pipeline=tuple(payload["required_pipeline"]),
        proven_evidence=tuple(payload["proven_phase5_evidence"]),
        not_yet_proven=tuple(payload["not_yet_proven"]),
        truth_authority=payload["truth_authority"],
    )
    if not report.verified:
        raise AfriRideGAeLiveWorkflowValidationError("GA eLive workflow report is not verified")
    return report


def _load_workflow_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(ga_elive_workflow:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideGAeLiveWorkflowValidationError("missing ga_elive_workflow yaml block")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(data.get("ga_elive_workflow"), dict):
        raise AfriRideGAeLiveWorkflowValidationError("invalid ga_elive_workflow yaml block")
    return data["ga_elive_workflow"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideGAeLiveWorkflowValidationError(f"missing phrase: {phrase}")


def format_summary(report: AfriRideGAeLiveWorkflowReport) -> str:
    return "\n".join(
        (
            "AfriRide GA eLive workflow validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"pipeline_stages={len(report.pipeline)}",
            f"proven_evidence={len(report.proven_evidence)}",
            f"not_yet_proven={len(report.not_yet_proven)}",
            f"truth_authority={report.truth_authority}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRideGAeLiveWorkflowValidationError as exc:
        print(f"AfriRide GA eLive workflow validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
