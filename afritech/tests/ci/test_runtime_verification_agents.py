from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from afritech.ci import (
    afriprog_agent_non_authority_validator,
    afriprog_contract_monitoring_validator,
    afriprog_drift_detection_validator,
    afriprog_drift_proposal_validator,
    afriprog_runtime_observation_integrity_validator,
)
from afritech.runtime_verification import (
    build_drift_context,
    classify_drift,
    coordinate_agents,
    detect_drift,
    drift_to_proposal,
    evaluate_contracts,
    observe_runtime,
)

ROOT = Path(__file__).resolve().parents[3]


def test_contract_drift_is_detected_from_runtime_observation() -> None:
    observation = _invalid_order_observation()
    evaluation = evaluate_contracts(observation)
    drift = detect_drift(observation, evaluation)

    assert evaluation["compliant"] is False
    assert drift is not None
    assert drift["type"] == "state_violation"
    assert drift["activation_allowed"] is False
    assert drift["runtime_mutation_allowed"] is False


def test_compliant_observation_does_not_emit_drift() -> None:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Paid",
        expected_state="Paid",
        observed_state="Paid",
        contract="order_must_be_paid_before_shipping",
    )

    assert detect_drift(observation, evaluate_contracts(observation)) is None


def test_drift_to_proposal_requires_governance_and_replay() -> None:
    drift = classify_drift(detect_drift(_invalid_order_observation(), evaluate_contracts(_invalid_order_observation())) or {})
    context = build_drift_context(
        drift,
        timestamp="2026-06-06T00:00:00Z",
        affected_files=("contracts/order.yaml",),
    )
    proposal = drift_to_proposal(drift, context).canonical_dict()

    assert context["replay_sufficient"] is True
    assert proposal["governance_required"] is True
    assert proposal["replay_required"] is True
    assert proposal["rollback_required"] is True
    assert proposal["activation_allowed"] is False
    assert proposal["runtime_mutation_allowed"] is False


def test_agent_coordination_is_non_authoritative() -> None:
    drift = classify_drift(detect_drift(_invalid_order_observation(), evaluate_contracts(_invalid_order_observation())) or {})
    coordinated = coordinate_agents((drift, drift, drift))

    assert coordinated["status"] == "drift_observed"
    assert coordinated["governance_required"] is True
    assert coordinated["activation_allowed"] is False
    assert coordinated["runtime_mutation_allowed"] is False
    assert coordinated["rollback_execution_allowed"] is False


def test_drift_cli_proposal_surface_is_blocked() -> None:
    completed = subprocess.run(
        (sys.executable, "-m", "afritech.cli.main", "drift-propose", "--json"),
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = json.loads(completed.stdout)

    assert payload["governance_review_required"] is True
    assert payload["activation_allowed"] is False
    assert payload["runtime_mutation_allowed"] is False
    assert payload["proposal"]["governance_required"] is True
    assert payload["proposal"]["activation_allowed"] is False


def test_runtime_verification_validators_pass_directly() -> None:
    afriprog_drift_detection_validator.validate()
    afriprog_contract_monitoring_validator.validate()
    afriprog_drift_proposal_validator.validate()
    afriprog_agent_non_authority_validator.validate()
    afriprog_runtime_observation_integrity_validator.validate()


def _invalid_order_observation() -> dict[str, object]:
    return observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
        trace=("OrderCreated", "OrderShipped"),
    )
