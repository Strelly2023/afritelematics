from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/pilot/AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_phase3_spec_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "Status: PHASE 3 LIVE OPERATIONS AND MONITORING GOVERNANCE SPEC" in text
    assert "Classification: LIVE_OPERATIONS_REPLAY_LINKED_MONITORING_GATE" in text
    assert "This specification is not live production success evidence." in text

    for item in (
        "global production readiness",
        "mass-market reliability",
        "all incidents automatically recover",
        "all alerts are perfect",
        "all operator actions are correct",
    ):
        assert item in lowered


def test_phase3_spec_defines_replay_linked_monitoring_contract() -> None:
    text = read_doc()

    for item in (
        "cutover gate completed",
        "BIND-001-phase1-phase2.yaml",
        "observability explains trace-backed state",
        "observability never overrides trace-backed state",
        "Phase 3 Execution Layer",
        "live monitoring dashboard (replay-backed)",
        "operator alert rules (evidence-driven)",
        "anomaly detection on trace chain",
        "real-time replay verification",
        "replay health summary",
        "guard violation board",
        "trace lookup by `ride_id`",
        "replay divergence alert",
        "token/auth anomaly alert",
    ):
        assert item in text


def test_phase3_spec_preserves_operator_boundaries_and_stop_conditions() -> None:
    text = read_doc()

    for item in (
        "mutate truth from observability surfaces",
        "declare replay valid without replay evidence",
        "declare receipt valid without receipt evidence",
        "bypass trace-backed investigation",
        "acknowledge evidence-complete alerts",
        "request replay rerun through governed tooling",
        "replay divergence detected",
        "receipt hash changes for same governed ride",
        "observability surface becomes authoritative",
    ):
        assert item in text


def test_phase3_spec_preserves_claim_discipline() -> None:
    text = read_doc()

    for item in (
        "live operations are governed by replay-linked monitoring and bounded operator procedures",
        "production proven",
        "global launch approved",
        "all scaling risks removed",
        "all monitoring complete forever",
    ):
        assert item in text


def test_phase3_spec_defines_dashboard_alert_anomaly_and_realtime_replay_details() -> None:
    text = read_doc()

    for item in (
        "Required dashboard panels",
        "replay divergence queue",
        "receipt stability board",
        "every dashboard card links to ride_id or trace_id",
        "Required alert rules",
        "alert_id",
        "evidence_pointer",
        "sequence gap anomaly",
        "invalid previous_hash anomaly",
        "anomaly detection may not redefine truth",
        "Required real-time replay checks",
        "ride request replay check",
        "receipt issuance replay check",
        "verification_status=VERIFIED",
        "verification_status=REJECTED",
        "replay verification snapshots",
        "anomaly detection outputs",
        "alert payload exports",
    ):
        assert item in text
