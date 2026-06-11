from __future__ import annotations

import json

from afritech.compliance.audit_export_tooling import export_enterprise_audit_bundle
from afritech.monitoring.realtime_anomaly_alerting import build_realtime_anomaly_alerts
from afritech.partner_verification import build_partner_verification_packet


def test_enterprise_audit_bundle_writes_trace_and_replay_bound_export(tmp_path) -> None:
    packet = build_partner_verification_packet(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash="a" * 64,
        replay_hash="b" * 64,
        receipt_hash="c" * 64,
        authority_hash="d" * 64,
        execution_fingerprint="e" * 64,
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-audit-001",
    )
    alerts = build_realtime_anomaly_alerts(
        {"validation_failures": 1},
        ride_id="ride-001",
        trace_id="trace-001",
        event_id="event-001",
        actor_id="driver-001",
        device_id="device-001",
        replay_hash="b" * 64,
        opened_at="2026-06-08T00:00:00Z",
    )

    output_path = export_enterprise_audit_bundle(
        output_dir=tmp_path,
        verification_packet=packet,
        launch_artifact_id="launch-001",
        anomaly_alerts=alerts,
    )

    body = json.loads(output_path.read_text(encoding="utf-8"))
    assert body["launch_artifact_id"] == "launch-001"
    assert body["verification_packet"]["anchor_id"] == packet.anchor_id
    assert body["anomaly_alerts"][0]["trace_id"] == "trace-001"
    assert "trace and replay remain authority" in body["authority_boundary"]
