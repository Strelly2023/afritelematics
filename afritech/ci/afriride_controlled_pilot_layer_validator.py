"""Validate the AfriRide Controlled Pilot Layer contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DOC = ROOT / "docs/proof/AFRIRIDE_CONTROLLED_PILOT_LAYER.md"

REQUIRED_PIPELINE = (
    "adapter",
    "normalization",
    "ingestion",
    "edge_guard",
    "runtime_admission",
    "runtime_orchestration",
    "runtime_activation",
    "guard_engine",
    "core_engine_matching",
    "worker_execution",
    "event_log_storage",
    "proof_generation",
    "evaluation_engine",
    "replay_verification",
    "constitutional_receipt",
    "registry_seal",
)

REQUIRED_SURFACES = (
    "afritech.edge.adapter.runtime_adapter",
    "afritech.edge.normalization.normalizer",
    "afritech.edge.ingestion.queue_ingestor",
    "afritech.guards.edge_input_guard",
    "afritech.api.app",
    "afritech.execution.partition.router",
    "afritech.execution.worker.worker_pool",
    "afritech.core.engine",
    "afritech.core.matching_engine",
    "afritech.storage.event_log",
    "afritech.storage.event_schema",
    "afritech.storage.replay_engine",
    "afritech.proof.constitutional_receipt",
)

DETERMINISTIC_DECISIONS = (
    "ride_request_admission",
    "driver_selection",
    "retry_ordering",
    "timeout_handling",
    "state_transitions",
)

CANONICAL_FAILURES = (
    "DRIVER_DROPOUT",
    "DRIVER_REJECTION_CHAIN",
    "TIMEOUT_EXCEEDED",
)

CONTINUITY_SCENARIOS = (
    "connectivity_loss_recovery",
    "replay_reconstruction",
    "offline_driver_rejoin",
    "adversarial_coordination",
    "multi_epoch_recovery",
)

VALIDITY_RULE = (
    "admissible",
    "deterministic",
    "invariant_preserving",
    "replay_equivalent",
    "identity_stable",
    "trace_complete",
)

INVARIANT_CONTRACTS = (
    "proof_meaning",
    "authority_boundaries",
    "afriride_scope",
    "claim_discipline",
    "enforcement_integrity",
)

OBSERVABILITY_OUTPUTS = (
    "replay_hash",
    "decision_hash",
    "determinism_match",
    "execution_trace",
)

FORBIDDEN = (
    "direct_api_to_core_execution",
    "unnormalized_input",
    "runtime_discovery",
    "reflection_based_execution",
    "random_driver_selection",
    "live_map_lookup_execution_authority",
    "first_accept_race_condition",
    "undeclared_failure_execution",
    "production_readiness_claim",
    "global_scale_claim",
    "optimization_claim",
    "external_runtime_guarantee_claim",
)

FORBIDDEN_CLAIMS = (
    "production ready",
    "public launch ready",
    "global scale proven",
    "external runtime guarantees proven",
    "optimization proven",
)


class AfriRideControlledPilotLayerValidationError(RuntimeError):
    """Raised when the controlled pilot layer contract is not admissible."""


@dataclass(frozen=True)
class AfriRideControlledPilotLayerReport:
    schema: str
    status: str
    classification: str
    purpose: str
    pipeline: tuple[str, ...]
    continuity_scenarios: tuple[str, ...]
    truth_authority: str
    production_readiness_claimed: bool

    @property
    def verified(self) -> bool:
        return (
            self.schema == "afriride.controlled_pilot_layer.v1"
            and self.status == "controlled_pilot_design_contract"
            and self.classification
            == "ga_elite_closed_world_continuity_proof_environment"
            and self.purpose == "continuity_under_controlled_disruption"
            and self.pipeline == REQUIRED_PIPELINE
            and self.continuity_scenarios == CONTINUITY_SCENARIOS
            and self.truth_authority == "replay_only"
            and self.production_readiness_claimed is False
        )


def validate(path: Path = CONTRACT_DOC) -> AfriRideControlledPilotLayerReport:
    if not path.exists():
        raise AfriRideControlledPilotLayerValidationError(
            "controlled pilot layer contract missing"
        )

    text = path.read_text(encoding="utf-8")
    _require(text, "STATUS: CONTROLLED PILOT LAYER DESIGN CONTRACT")
    _require(text, "CLASSIFICATION: GA ELITE CLOSED-WORLD CONTINUITY PROOF ENVIRONMENT")
    _require(text, "It is not a production ride-hailing system.")
    _require(text, "Undeclared failure equals invalid execution.")
    _require(text, "Observability cannot change execution")

    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in lowered:
            raise AfriRideControlledPilotLayerValidationError(
                f"forbidden claim: {phrase}"
            )

    payload = _load_contract_payload(text)

    _require_equal(payload["required_pipeline"], REQUIRED_PIPELINE, "pipeline")
    _require_equal(
        payload["deterministic_decisions"],
        DETERMINISTIC_DECISIONS,
        "deterministic decisions",
    )
    _require_equal(payload["canonical_failures"], CANONICAL_FAILURES, "failures")
    _require_equal(
        payload["continuity_scenarios"],
        CONTINUITY_SCENARIOS,
        "continuity scenarios",
    )
    _require_equal(payload["validity_rule"], VALIDITY_RULE, "validity rule")
    _require_equal(
        payload["invariant_contracts"],
        INVARIANT_CONTRACTS,
        "invariant contracts",
    )
    _require_equal(
        payload["observability_outputs"],
        OBSERVABILITY_OUTPUTS,
        "observability outputs",
    )
    _require_equal(payload["forbidden"], FORBIDDEN, "forbidden violations")

    surfaces = payload["required_surfaces"]
    for surface in REQUIRED_SURFACES:
        if surfaces.get(surface) != "IMPLEMENTED":
            raise AfriRideControlledPilotLayerValidationError(
                f"surface is not IMPLEMENTED: {surface}"
            )

    if payload["production_readiness_claimed"] is not False:
        raise AfriRideControlledPilotLayerValidationError(
            "controlled pilot contract claims production readiness"
        )
    if payload["external_runtime_guarantees_claimed"] is not False:
        raise AfriRideControlledPilotLayerValidationError(
            "controlled pilot contract claims external runtime guarantees"
        )
    if payload["truth_authority"] != "replay_only":
        raise AfriRideControlledPilotLayerValidationError(
            "truth authority must remain replay_only"
        )
    if payload["execution_environment"] != "closed_world":
        raise AfriRideControlledPilotLayerValidationError(
            "execution environment must remain closed_world"
        )
    if payload["constitutional_pipeline_only"] is not True:
        raise AfriRideControlledPilotLayerValidationError(
            "constitutional pipeline must be the only admissibility path"
        )

    report = AfriRideControlledPilotLayerReport(
        schema=payload["schema"],
        status=payload["status"],
        classification=payload["classification"],
        purpose=payload["purpose"],
        pipeline=tuple(payload["required_pipeline"]),
        continuity_scenarios=tuple(payload["continuity_scenarios"]),
        truth_authority=payload["truth_authority"],
        production_readiness_claimed=payload["production_readiness_claimed"],
    )
    if not report.verified:
        raise AfriRideControlledPilotLayerValidationError(
            "controlled pilot layer report is not verified"
        )
    return report


def _load_contract_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```yaml\n(controlled_pilot_layer:.*?)\n```", text, re.DOTALL)
    if match is None:
        raise AfriRideControlledPilotLayerValidationError(
            "missing controlled_pilot_layer yaml block"
        )
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict) or not isinstance(
        data.get("controlled_pilot_layer"), dict
    ):
        raise AfriRideControlledPilotLayerValidationError(
            "invalid controlled_pilot_layer yaml block"
        )
    return data["controlled_pilot_layer"]


def _require(text: str, phrase: str) -> None:
    if phrase not in text:
        raise AfriRideControlledPilotLayerValidationError(f"missing phrase: {phrase}")


def _require_equal(value: object, expected: tuple[str, ...], label: str) -> None:
    if value != list(expected):
        raise AfriRideControlledPilotLayerValidationError(f"{label} mismatch")


def format_summary(report: AfriRideControlledPilotLayerReport) -> str:
    return "\n".join(
        (
            "AfriRide controlled pilot layer validation PASSED",
            f"schema={report.schema}",
            f"status={report.status}",
            f"classification={report.classification}",
            f"pipeline_stages={len(report.pipeline)}",
            f"continuity_scenarios={len(report.continuity_scenarios)}",
            f"truth_authority={report.truth_authority}",
            f"production_readiness_claimed={report.production_readiness_claimed}",
            f"verified={report.verified}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriRideControlledPilotLayerValidationError as exc:
        print(f"AfriRide controlled pilot layer validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
