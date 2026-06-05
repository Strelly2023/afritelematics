from __future__ import annotations

import pytest

from afritech.afritpps.observability import build_orchestration_view, list_orchestration_views
from afritech.afritpps.orchestration import AfriTPPSOrchestrationIntent, OrchestrationStep
from afritech.afritpps.persistent import create_persistent_orchestration


@pytest.mark.django_db
def test_orchestration_view_represents_pending_graph():
    create_persistent_orchestration(
        AfriTPPSOrchestrationIntent(
            orchestration_id="orch.view.001",
            name="View graph",
            operations=(
                OrchestrationStep(
                    step_id="a",
                    domain="AfriRide",
                    operation="TripCompleted",
                    actor_id="driver:D001",
                    subject_id="ride:view",
                    payload={"ride_id": "ride:view", "driver_id": "D001"},
                    signature={"signature_mode": "development_adapter"},
                ),
                OrchestrationStep(
                    step_id="b",
                    domain="AfriTalent",
                    operation="WorkCompleted",
                    actor_id="driver:D001",
                    subject_id="work:view",
                    payload={"worker_id": "D001", "work_id": "ride:view"},
                    signature={"signature_mode": "development_adapter"},
                    dependencies=("a",),
                ),
            ),
        )
    )

    view = build_orchestration_view("orch.view.001")
    listed = list_orchestration_views()

    assert view.status == "CREATED"
    assert view.steps[0].status == "PENDING"
    assert view.edges[0].canonical_dict() == {"from_step": "a", "to_step": "b"}
    assert listed[0]["orchestration_id"] == "orch.view.001"
