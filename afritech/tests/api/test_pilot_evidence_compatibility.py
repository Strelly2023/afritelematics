from __future__ import annotations

import time

from fastapi.testclient import TestClient

from afritech.api.app import app


def test_pilot_evidence_compatibility_ingests_signed_event_server_side() -> None:
    client = TestClient(app)
    event_id = f"pilot-test-{time.time_ns()}"

    response = client.post(
        "/pilot/evidence",
        headers={
            "X-AfriRide-Device-Id": "driver-test-device",
            "X-AfriRide-Event-Id": event_id,
        },
        json={
            "type": "driver_location_event",
            "driver_id": "driver-001",
            "surface": "driver_mobile",
            "payload": {
                "latitude": -37.8136,
                "longitude": 144.9631,
                "accuracy": 12,
                "app_version": "pilot-test",
                "test_mode": True,
            },
            "constraints": {
                "gps_accuracy_threshold_m": 50,
            },
            "verdict": "observed",
            "captured_at": "2026-06-30T09:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "captured"
    assert body["evidence_id"] == event_id
    assert body["node_id"] == "fastapi_event_ingestion"
    assert body["accepted"] == [event_id]
