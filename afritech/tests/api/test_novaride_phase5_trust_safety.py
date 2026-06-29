from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import PlatformStore
from afritech.api.app import app


def _issue_token(client: TestClient, *, role: str, organization_id: str, user_id: str) -> str:
    response = client.post(
        "/v1/auth/token",
        json={
            "user_id": user_id,
            "role": role,
            "organization_id": organization_id,
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_phase5_trust_safety_projection_and_safe_bridge(tmp_path) -> None:
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "phase5_trust_safety.sqlite3")

    try:
        client = TestClient(app)
        org_id = "org-phase5-trust-safety-001"

        operator_token = _issue_token(client, role="OPERATOR", organization_id=org_id, user_id="operator-1")
        passenger_1_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-1")
        passenger_2_token = _issue_token(client, role="CUSTOMER", organization_id=org_id, user_id="passenger-2")
        driver_1_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-1")
        driver_2_token = _issue_token(client, role="DRIVER", organization_id=org_id, user_id="driver-2")
        operator_headers = {"Authorization": f"Bearer {operator_token}"}
        passenger_1_headers = {"Authorization": f"Bearer {passenger_1_token}"}
        passenger_2_headers = {"Authorization": f"Bearer {passenger_2_token}"}
        driver_1_headers = {"Authorization": f"Bearer {driver_1_token}"}
        driver_2_headers = {"Authorization": f"Bearer {driver_2_token}"}

        onboard = client.post(
            "/v1/novatech/phase0/organizations/onboard",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "legal_name": "Phase 5 Trust Safety Mobility Pty Ltd",
                "sector": "mobility",
                "trust_domain": "novaride",
            },
        )
        assert onboard.status_code == 200

        subscription = client.post(
            "/v1/novatech/phase0/subscriptions",
            headers=operator_headers,
            json={
                "organization_id": org_id,
                "plan": "enterprise",
                "status": "active",
                "billing_cycle": "monthly",
                "seats": 12,
            },
        )
        assert subscription.status_code == 200

        store = control_plane._STORE
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-1",
            status="online",
            location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            trust_score=96,
            metadata={"zone": "CBD"},
        )
        store.store_driver_presence(
            organization_id=org_id,
            driver_id="driver-2",
            status="online",
            location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            trust_score=72,
            metadata={"zone": "Southbank"},
        )

        store.store_ride(
            ride_id="ride-1",
            organization_id=org_id,
            passenger_id="passenger-1",
            driver_id="driver-1",
            pickup_location={"lat": -37.8136, "lng": 144.9631, "label": "CBD"},
            destination_location={"lat": -37.8200, "lng": 144.9500, "label": "Docklands"},
            fare_estimate="40.00",
            currency="AUD",
            status="completed",
            final_fare="40.00",
            completed_at="2026-06-28T10:00:00+00:00",
        )
        store.store_ride(
            ride_id="ride-2",
            organization_id=org_id,
            passenger_id="passenger-2",
            driver_id="driver-2",
            pickup_location={"lat": -37.8150, "lng": 144.9700, "label": "Southbank"},
            destination_location={"lat": -37.8200, "lng": 144.9800, "label": "Richmond"},
            fare_estimate="35.00",
            currency="AUD",
            status="cancelled",
        )

        store.record_audit_event(
            organization_id=org_id,
            event_type="fraud_suspected",
            actor_user_id="operator-1",
            actor_role="OPERATOR",
            target="ride-2",
            status="flagged",
            payload={"reason": "payment tamper detected"},
        )
        store.record_audit_event(
            organization_id=org_id,
            event_type="trip_anomaly_detected",
            actor_user_id="operator-1",
            actor_role="OPERATOR",
            target="ride-1",
            status="open",
            payload={"reason": "route deviation"},
        )
        store.record_audit_event(
            organization_id=org_id,
            event_type="sos_triggered",
            actor_user_id="passenger-1",
            actor_role="CUSTOMER",
            target="ride-1",
            status="open",
            payload={"reason": "emergency escalation"},
        )

        policy = store.store_zero_trust_policy(
            organization_id=org_id,
            policy_name="driver_blacklist",
            version="1.0.0",
            rule_type="deny_dispatch",
            rule_payload={"blocked_subjects": ["driver-2"]},
            active=True,
            created_by="operator-1",
        )
        decision = store.store_zero_trust_decision(
            organization_id=org_id,
            policy_id=policy["policy_id"],
            subject="driver-2",
            action="deny_dispatch",
            resource="driver-2",
            allowed=False,
            reason="blacklist_suspicious_activity",
            context={"ride_id": "ride-2", "source": "operator_review"},
        )
        assert decision["allowed"] is False

        trust_score = store.store_trust_score(
            organization_id=org_id,
            trust_score=84,
            classification="watch",
            breakdown={
                "fraud": 1,
                "anomaly": 1,
                "sos": 1,
                "operational_trust": 84,
            },
            findings=["manual review", "bounded execution hold"],
        )
        assert trust_score["trust_score"] == 84

        notification = store.queue_notification(
            organization_id=org_id,
            recipient_id="operator-1",
            channel="push",
            message="SOS escalation requires review",
        )
        assert notification["status"] == "queued"

        trust_safety = client.get(
            "/v1/novaride/phase5/trust-safety",
            headers=operator_headers,
            params={"organization_id": org_id, "limit": 50},
        )
        assert trust_safety.status_code == 200
        payload = trust_safety.json()
        assert payload["view"] == "novaride_phase5_trust_safety"
        assert payload["ratings"]["drivers"]
        assert payload["ratings"]["riders"]
        assert payload["trust"]["overall_trust_score"] >= 0
        assert payload["fraud_detection"]["count"] >= 1
        assert payload["trip_anomaly_detection"]["count"] >= 1
        assert payload["sos"]["open_count"] >= 1
        assert payload["blacklist"]["count"] >= 1
        assert payload["auto_execution_bridge"]["safe_limit_rules"]["projection_only"] is True
        assert payload["auto_execution_bridge"]["safe_limit_rules"]["read_only"] is True
        assert payload["auto_execution_bridge"]["governance_linked"] is True
        assert payload["auto_execution_bridge"]["creates_authority"] is False
        assert payload["guardrails"]["tenant_isolation_preserved"] is True
        assert payload["read_only"] is True
        assert payload["projection_only"] is True

        status = client.get("/v1/novaride/phase5/status", headers=operator_headers, params={"limit": 50})
        assert status.status_code == 200
        status_payload = status.json()
        assert status_payload["trust_safety"]["view"] == "novaride_phase5_trust_safety"
        assert status_payload["readiness"]["trust_safety_ready"] is True
        assert status_payload["readiness"]["auto_execution_bridge_ready"] is True

        forbidden = client.get(
            "/v1/novaride/phase5/trust-safety",
            headers=operator_headers,
            params={"organization_id": "spoofed-org"},
        )
        assert forbidden.status_code == 403
        assert "organization_isolation_violation" in forbidden.text
    finally:
        control_plane._STORE = original_store
