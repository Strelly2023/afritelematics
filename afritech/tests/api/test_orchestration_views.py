from __future__ import annotations

import pytest
from django.test import Client

from afritech.afritpps.orchestration import AfriTPPSOrchestrationIntent, OrchestrationStep
from afritech.afritpps.persistent import create_persistent_orchestration


@pytest.mark.django_db
def test_orchestration_api_lists_details_and_controls_flow():
    create_persistent_orchestration(
        AfriTPPSOrchestrationIntent(
            orchestration_id="orch.api.001",
            name="API graph",
            operations=(
                OrchestrationStep(
                    step_id="trip",
                    domain="AfriRide",
                    operation="TripCompleted",
                    actor_id="driver:D001",
                    subject_id="ride:api",
                    payload={"ride_id": "ride:api", "driver_id": "D001"},
                    signature={"signature_mode": "development_adapter"},
                ),
            ),
        )
    )
    client = Client()

    listed = client.get("/api/orchestrations", HTTP_ACCEPT="application/json")
    detail = client.get("/api/orchestrations/orch.api.001", HTTP_ACCEPT="application/json")
    paused = client.post(
        "/api/orchestrations/orch.api.001/pause",
        data={"operator_id": "operator:001", "reason": "review"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    resumed = client.post(
        "/api/orchestrations/orch.api.001/resume",
        data={"operator_id": "operator:001", "reason": "continue"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    aborted = client.post(
        "/api/orchestrations/orch.api.001/abort",
        data={"operator_id": "operator:001", "reason": "stop"},
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )

    assert listed.status_code == 200
    assert listed.json()["orchestrations"][0]["orchestration_id"] == "orch.api.001"
    assert detail.status_code == 200
    assert detail.json()["steps"][0]["step_id"] == "trip"
    assert paused.json()["status"] == "PAUSED"
    assert resumed.json()["status"] == "PARTIAL_PROGRESS"
    assert aborted.json()["status"] == "ABORTED"
