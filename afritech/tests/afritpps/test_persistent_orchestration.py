from __future__ import annotations

import pytest

from afritech.afritpps.observability import build_orchestration_view
from afritech.afritpps.orchestration import AfriTPPSOrchestrationIntent, OrchestrationStep
from afritech.afritpps.persistent import (
    OperatorControlError,
    abort_orchestration,
    create_persistent_orchestration,
    execute_persistent_orchestration,
    pause_orchestration,
    resume_orchestration,
)
from afritech.models import OperatorActionLog, OrchestrationStepState


@pytest.mark.django_db
def test_persistent_orchestration_execution_builds_verified_graph_view():
    intent = _intent("orch.persist.001")

    outcome = execute_persistent_orchestration(intent)
    view = build_orchestration_view("orch.persist.001")

    assert outcome.fully_verified is True
    assert view.status == "COMPLETED"
    assert view.fully_verified is True
    assert len(view.steps) == 2
    assert view.steps[0].status == "VERIFIED"
    assert view.edges[0].from_step == "trip_completed"
    assert view.edges[0].to_step == "work_completed"
    assert view.canonical_dict()["percent_complete"] == 100


@pytest.mark.django_db
def test_operator_controls_change_flow_state_without_mutating_truth():
    create_persistent_orchestration(_intent("orch.control.001"))

    paused = pause_orchestration(
        "orch.control.001",
        operator_id="operator:001",
        reason="inspect",
    )
    resumed = resume_orchestration(
        "orch.control.001",
        operator_id="operator:001",
        reason="continue",
    )
    aborted = abort_orchestration(
        "orch.control.001",
        operator_id="operator:001",
        reason="manual stop",
    )

    assert paused.status == "PAUSED"
    assert resumed.status == "PARTIAL_PROGRESS"
    assert aborted.status == "ABORTED"
    assert OperatorActionLog.objects.count() == 3
    assert OrchestrationStepState.objects.filter(status="SKIPPED").count() == 2


@pytest.mark.django_db
def test_operator_controls_reject_invalid_state_transitions():
    create_persistent_orchestration(_intent("orch.invalid.control"))

    with pytest.raises(OperatorControlError, match="only paused"):
        resume_orchestration(
            "orch.invalid.control",
            operator_id="operator:001",
        )


def _intent(orchestration_id: str) -> AfriTPPSOrchestrationIntent:
    return AfriTPPSOrchestrationIntent(
        orchestration_id=orchestration_id,
        name="Persistent driver flow",
        operations=(
            OrchestrationStep(
                step_id="trip_completed",
                domain="AfriRide",
                operation="TripCompleted",
                actor_id="driver:D001",
                subject_id=f"ride:{orchestration_id}",
                payload={"ride_id": f"ride:{orchestration_id}", "driver_id": "D001"},
                signature={"signature_mode": "development_adapter"},
            ),
            OrchestrationStep(
                step_id="work_completed",
                domain="AfriTalent",
                operation="WorkCompleted",
                actor_id="driver:D001",
                subject_id=f"work:{orchestration_id}",
                payload={"worker_id": "D001", "work_id": f"ride:{orchestration_id}"},
                signature={"signature_mode": "development_adapter"},
                dependencies=("trip_completed",),
            ),
        ),
    )
