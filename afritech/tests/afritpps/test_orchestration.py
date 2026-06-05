from __future__ import annotations

import pytest

from afritech.afritpps.orchestration import (
    AfriTPPSOrchestrationError,
    AfriTPPSOrchestrationIntent,
    OrchestrationStep,
    execute_orchestration,
)


@pytest.mark.django_db
def test_orchestration_executes_cross_domain_dependency_graph():
    outcome = execute_orchestration(
        AfriTPPSOrchestrationIntent(
            orchestration_id="orch.driver.lifecycle.001",
            name="Driver lifecycle",
            operations=(
                OrchestrationStep(
                    step_id="trip_completed",
                    domain="AfriRide",
                    operation="TripCompleted",
                    actor_id="driver:D001",
                    subject_id="ride:001",
                    payload={"ride_id": "ride:001", "driver_id": "D001"},
                    signature={"signature_mode": "development_adapter"},
                ),
                OrchestrationStep(
                    step_id="work_completed",
                    domain="AfriTalent",
                    operation="WorkCompleted",
                    actor_id="driver:D001",
                    subject_id="work:ride:001",
                    payload={"worker_id": "D001", "work_id": "ride:001"},
                    signature={"signature_mode": "development_adapter"},
                    dependencies=("trip_completed",),
                ),
                OrchestrationStep(
                    step_id="health_check",
                    domain="AfriHealth",
                    operation="HealthCheckTriggered",
                    actor_id="operator:health",
                    subject_id="health:D001",
                    payload={"driver_id": "D001", "reason": "post_trip_check"},
                    signature={"signature_mode": "development_adapter"},
                    dependencies=("trip_completed",),
                ),
            ),
        )
    )

    assert outcome.fully_verified is True
    assert outcome.status == "verified"
    assert list(outcome.step_results) == [
        "trip_completed",
        "work_completed",
        "health_check",
    ]
    assert outcome.step_results["trip_completed"].domain == "AfriRide"
    assert outcome.step_results["work_completed"].domain == "AfriTalent"
    assert outcome.step_results["health_check"].domain == "AfriHealth"
    assert len(outcome.final_state_hash) == 64


def test_orchestration_rejects_unknown_dependency():
    with pytest.raises(AfriTPPSOrchestrationError, match="unknown dependency"):
        execute_orchestration(
            AfriTPPSOrchestrationIntent(
                orchestration_id="orch.bad.dep",
                name="Bad dependency",
                operations=(
                    OrchestrationStep(
                        step_id="step_1",
                        domain="AfriRide",
                        operation="TripCompleted",
                        actor_id="driver:D001",
                        subject_id="ride:001",
                        payload={"ride_id": "ride:001", "driver_id": "D001"},
                        signature={"signature_mode": "development_adapter"},
                        dependencies=("missing",),
                    ),
                ),
            )
        )


def test_orchestration_rejects_cyclic_dependencies():
    with pytest.raises(AfriTPPSOrchestrationError, match="cyclic"):
        execute_orchestration(
            AfriTPPSOrchestrationIntent(
                orchestration_id="orch.cycle",
                name="Cycle",
                operations=(
                    OrchestrationStep(
                        step_id="a",
                        domain="AfriRide",
                        operation="TripCompleted",
                        actor_id="driver:D001",
                        subject_id="ride:001",
                        payload={"ride_id": "ride:001", "driver_id": "D001"},
                        signature={"signature_mode": "development_adapter"},
                        dependencies=("b",),
                    ),
                    OrchestrationStep(
                        step_id="b",
                        domain="AfriTalent",
                        operation="WorkCompleted",
                        actor_id="driver:D001",
                        subject_id="work:001",
                        payload={"worker_id": "D001", "work_id": "ride:001"},
                        signature={"signature_mode": "development_adapter"},
                        dependencies=("a",),
                    ),
                ),
            )
        )


@pytest.mark.django_db
def test_orchestration_fails_closed_when_step_contract_fails():
    with pytest.raises(Exception, match="DESIGNED_BLOCKED"):
        execute_orchestration(
            AfriTPPSOrchestrationIntent(
                orchestration_id="orch.pay.blocked",
                name="Blocked payment",
                operations=(
                    OrchestrationStep(
                        step_id="payment",
                        domain="AfriPay",
                        operation="RawTransactionEvidence",
                        actor_id="operator:001",
                        subject_id="tx:001",
                        payload={
                            "transaction_id": "tx:001",
                            "payer": "rider",
                            "payee": "driver",
                            "amount": 10,
                            "currency": "AUD",
                            "method": "cash",
                            "outcome": "completed",
                        },
                        signature={"signature_mode": "development_adapter"},
                    ),
                ),
            )
        )
