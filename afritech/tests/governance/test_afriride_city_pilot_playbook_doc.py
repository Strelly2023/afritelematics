from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/operations/AfriRide_City_Level_Pilot_Deployment_Playbook.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_city_pilot_playbook_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "STATUS: BOUNDED OPERATIONAL PILOT PLAN" in text
    assert "CLASSIFICATION: PILOT READINESS PLANNING SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not evidence that AfriRide has completed a real-world city pilot".lower() in lowered
    assert "controlled city pilot completed" in text
    assert "global deployment readiness achieved" in text


def test_city_pilot_playbook_defines_melbourne_and_burundi_sequence() -> None:
    text = read_doc()

    for required in (
        "Melbourne Airport <-> Melbourne CBD corridor",
        "drivers: 10-25",
        "riders: 50-200 invite-only",
        "trip_volume: 50-150 trips/day",
        "Burundi is the recommended second pilot",
        "unstable mobile networks",
        "cash plus mobile-money payment observations",
    ):
        assert required in text


def test_city_pilot_playbook_preserves_constitutional_pipeline() -> None:
    text = read_doc()

    for stage in (
        "Driver / Rider App",
        "-> Edge Adapter",
        "-> Normalization",
        "-> Admission",
        "-> Queue",
        "-> Execution Engine",
        "-> Witness Store",
        "-> Replay System",
    ):
        assert stage in text

    assert "No mobile client, public API, payment observation, or GPS reading may call core" in text


def test_city_pilot_playbook_defines_required_validation_domains() -> None:
    text = read_doc()

    for domain in (
        "Real Trip Execution",
        "GPS Reality vs Normalization",
        "Network Behavior",
        "Client Chaos",
        "Security Layer",
        "Market Dynamics",
    ):
        assert domain in text

    for evidence in (
        "trip_replay_trace",
        "normalized_gps_trace",
        "network_event_replay",
        "clock_drift_normalization_receipt",
        "payload_tamper_rejection_trace",
        "pricing_replay_equivalence",
        "fairness_trace_validation",
    ):
        assert evidence in text


def test_city_pilot_playbook_defines_metrics_and_rollout_gates() -> None:
    text = read_doc()

    for metric in (
        "replay_success: 100%",
        "trace_completeness: 100%",
        "determinism_variance: 0",
        "convergence_failure: 0",
        "trip_completion: greater than 95%",
        "driver_acceptance: greater than 80%",
        "forged_event_success: 0",
        "unauthorized_mutation: 0",
    ):
        assert metric in text

    for phase in (
        "Phase 1 - Internal Pilot",
        "Phase 2 - Controlled Users",
        "Phase 3 - Open Pilot",
        "pilot_scope_receipt",
        "real_trip_reconstruction",
        "production_replay_trace",
    ):
        assert phase in text
