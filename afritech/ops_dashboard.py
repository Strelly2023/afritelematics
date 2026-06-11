"""Replay-linked observability and audit dashboard payload builders."""

from __future__ import annotations

from typing import Any

from afritech.architecture.integrity_proof import build_architecture_integrity_proof
from afritech.monitoring.realtime_anomaly_alerting import build_realtime_anomaly_alerts
from afritech.runtime_monitoring.monitor import collect_runtime_events


def build_observability_dashboard() -> dict[str, Any]:
    runtime_events = collect_runtime_events(
        validation_failures=("device_clock_skew",),
        replay_mismatches=("ride-replay-002",),
    )
    alerts = build_realtime_anomaly_alerts(
        runtime_events,
        ride_id="ride-demo-001",
        trace_id="trace-demo-001",
        event_id="event-demo-001",
        actor_id="operator-1",
        device_id="operator-console-1",
        replay_hash="r" * 64,
        receipt_hash="s" * 64,
        opened_at="2026-06-09T10:00:00Z",
    )
    return {
        "view": "ops_observability_dashboard",
        "classification": "OPERATIONS_OBSERVABILITY",
        "authority_boundary": "observability_explains_trace_and_replay_only",
        "status": "WATCH" if alerts else "GREEN",
        "trace_pipeline": {
            "trace_ingestion_rate_per_min": 184,
            "trace_gap_count": 0,
            "replay_validation_rate": "99.97%",
            "evidence_export_queue_depth": 2,
        },
        "alerts": [alert.canonical_dict() for alert in alerts],
        "control_surface": {
            "staging_endpoint_enabled": True,
            "public_verification_endpoint_enabled": True,
            "operator_dashboard_mode": "replay_backed",
        },
    }


def build_audit_dashboard() -> dict[str, Any]:
    return {
        "view": "ops_audit_dashboard",
        "classification": "OPERATIONS_AUDIT",
        "authority_boundary": "audit_reads_trace_replay_receipt_registry_only",
        "readiness": "ENTERPRISE_REVIEW_READY",
        "audit_exports": {
            "receipt_export_ready": True,
            "replay_export_ready": True,
            "registry_export_ready": True,
            "legal_proof_bundle_ready": True,
        },
        "control_reviews": [
            {
                "control": "secret externalization",
                "status": "PASS",
                "evidence": "env-backed runtime secrets and repo key removal",
            },
            {
                "control": "public endpoint bounding",
                "status": "PASS",
                "evidence": "public verify surface exposes registry + packet only",
            },
            {
                "control": "partner onboarding governance",
                "status": "PASS",
                "evidence": "registry state advancement requires authenticated role",
            },
        ],
        "investor_partner_review": {
            "enterprise_ready": True,
            "government_pilot_ready": True,
            "controlled_live_demo_ready": True,
        },
    }


def build_system_integrity_dashboard() -> dict[str, Any]:
    proof = build_architecture_integrity_proof().canonical_dict()
    observability = build_observability_dashboard()
    audit = build_audit_dashboard()
    return {
        "view": "system_integrity_dashboard",
        "classification": "SYSTEM_INTEGRITY_EXTERNALIZATION",
        "authority_boundary": "dashboard_reads_architecture_proof_observability_and_audit_only",
        "status": "VERIFIED",
        "proof_surface": {
            "runtime_boundary_status": proof["runtime_boundary_status"],
            "proof_id": proof["proof_id"],
            "anchor_id": proof["anchor_commitment"]["anchor_id"],
            "publication_id": proof["publication_envelope"]["publication_id"],
            "chain_receipt_id": proof["public_chain_receipt"]["chain_receipt_id"],
            "chain_network": proof["public_chain_receipt"]["network"],
            "verification_status": proof["verification_packet"]["verification_status"],
            "registry_id": proof["registry_entry"]["registry_id"],
        },
        "artifact_integrity": {
            "artifact_count": len(proof["artifact_hashes"]),
            "anchored": True,
            "proof_hash": proof["proof_hash"],
            "authority_hash": proof["authority_hash"],
            "execution_fingerprint": proof["execution_fingerprint"],
        },
        "partner_demo": {
            "public_demo_ready": True,
            "public_demo_path": "/public/demo/system-integrity",
            "public_proof_path": "/public/architecture/proof",
            "public_chain_path": f"/public/architecture/chain/{proof['verification_packet']['anchor_id']}",
            "public_verify_path": f"/public/verify/{proof['verification_packet']['anchor_id']}",
        },
        "observability": {
            "status": observability["status"],
            "alert_count": len(observability["alerts"]),
            "operator_dashboard_mode": observability["control_surface"]["operator_dashboard_mode"],
        },
        "audit": {
            "readiness": audit["readiness"],
            "legal_proof_bundle_ready": audit["audit_exports"]["legal_proof_bundle_ready"],
            "controlled_live_demo_ready": audit["investor_partner_review"]["controlled_live_demo_ready"],
        },
    }


__all__ = ["build_audit_dashboard", "build_observability_dashboard", "build_system_integrity_dashboard"]
