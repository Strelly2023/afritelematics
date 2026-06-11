from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


DOC = (
    Path(__file__).resolve().parents[3]
    / "afritech/docs/operations/afriride_city_pilot_playbook.md"
)


def load_playbook() -> dict[str, Any]:
    text = DOC.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    assert match is not None
    payload = yaml.safe_load(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_playbook_scope_constraints() -> None:
    playbook = load_playbook()

    assert "explicitly_not_claimed" in playbook["scope"]

    forbidden = [
        "global scalability",
        "production readiness",
        "economic optimality",
    ]

    for item in forbidden:
        assert item in playbook["scope"]["explicitly_not_claimed"]


def test_required_metrics() -> None:
    playbook = load_playbook()
    metrics = playbook["metrics"]

    required = [
        "replay_success_rate",
        "trace_completeness",
        "convergence_divergence",
        "determinism_variance",
        "replay_divergence_detection",
        "token_replay_rejection",
        "observability_trace_linkage",
    ]

    for key in required:
        assert key in metrics


def test_required_scenarios() -> None:
    playbook = load_playbook()
    scenario_names = [scenario["name"] for scenario in playbook["scenarios"]]

    required = [
        "trip_execution",
        "gps_noise",
        "offline_sync",
        "device_token_lifecycle",
        "adversarial_injection",
        "failure_injection_determinism_break",
        "network_delay",
        "surge_conditions",
    ]

    for scenario in required:
        assert scenario in scenario_names


def test_failure_conditions_exist() -> None:
    playbook = load_playbook()

    assert "failure_conditions" in playbook
    assert len(playbook["failure_conditions"]) > 0


def test_pipeline_integrity() -> None:
    playbook = load_playbook()
    pipeline = playbook["event_pipeline"]

    required_steps = [
        "edge_ingestion",
        "normalization",
        "admission",
        "execution",
        "witness",
        "replay",
    ]

    for step in required_steps:
        assert step in pipeline


def test_pilot_zones_are_ordered_and_bounded() -> None:
    playbook = load_playbook()
    zones = playbook["zones"]

    assert zones["melbourne"]["first"] is True
    assert zones["melbourne"]["area"] == "airport_to_cbd"
    assert zones["burundi"]["second"] is True
    assert zones["burundi"]["area"] == "bujumbura_core"


def test_evidence_package_requires_replay_backed_outputs() -> None:
    playbook = load_playbook()
    evidence = playbook["evidence_package"]

    for required in (
        "pilot_scope_receipt",
        "normalized_event_trace",
        "authenticated_mutation_trace",
        "device_registration_snapshot",
        "token_lifecycle_audit",
        "convergence_trace_validation",
        "replay_divergence_receipt",
        "observability_trace_export",
        "real_trip_reconstruction",
    ):
        assert required in evidence


def test_observability_section_stays_trace_and_replay_linked() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "Observability Design Tied to Trace/Replay",
        "trace_id",
        "device_id",
        "token_jti",
        "replay_hash",
        "receipt_hash",
        "device and token exception board",
        "replay divergence board",
        "failure injection evidence board",
        "must resolve back to trace evidence and replay-derived outputs",
    ):
        assert required in text
