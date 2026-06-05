from __future__ import annotations

from afritech.distributed.services.state_service import StateService
from afritech.services.africonnecttl.contracts import (
    AUTHORITY_BOUNDARY,
    assert_claim_allowed,
)
from afritech.services.africonnecttl.execution import (
    AFRICONNECTTL_FN_IDS,
    build_operation,
    execute_operation,
)
from afritech.services.africonnecttl.reducers import shipment_reducer


def test_africonnecttl_authority_boundary_stays_planned_only():
    boundary = AUTHORITY_BOUNDARY.to_dict()

    assert boundary["status"] == "PLANNED"
    assert boundary["operational_proof"] == "NONE"
    assert boundary["field_execution"] == "NONE"
    assert boundary["live_deployment"] == "FORBIDDEN"

    assert_claim_allowed("controlled_simulation")
    try:
        assert_claim_allowed("production readiness")
    except RuntimeError as exc:
        assert "forbids claim" in str(exc)
    else:
        raise AssertionError("production readiness claim must be forbidden")


def test_africonnecttl_required_fn_ids_are_registered():
    assert AFRICONNECTTL_FN_IDS == (
        "shipment_request",
        "shipment_assign",
        "shipment_pickup",
        "shipment_transit",
        "shipment_delivered",
    )


def test_africonnecttl_controlled_shipment_flow_projects_state():
    state: dict[str, object] = {}

    events = [
        execute_operation(
            "shipment_request",
            None,
            {
                "shipment_id": "shipment-001",
                "sender_id": "sender-001",
                "receiver_id": "receiver-001",
                "origin": "Kampala",
                "destination": "Entebbe",
            },
        ),
        execute_operation(
            "shipment_assign",
            None,
            {
                "shipment_id": "shipment-001",
                "courier_id": "courier-001",
            },
        ),
        execute_operation(
            "shipment_pickup",
            None,
            {
                "shipment_id": "shipment-001",
                "courier_id": "courier-001",
            },
        ),
        execute_operation(
            "shipment_transit",
            None,
            {
                "shipment_id": "shipment-001",
                "location": "Kajansi",
            },
        ),
        execute_operation(
            "shipment_delivered",
            None,
            {
                "shipment_id": "shipment-001",
                "receiver_id": "receiver-001",
                "proof_of_delivery": "receiver-confirmed",
            },
        ),
    ]

    for event in events:
        state = shipment_reducer(state, event)

    service = StateService(initial_state=state)
    shipment = service.get_shipment("shipment-001")

    assert shipment is not None
    assert shipment["status"] == "DELIVERED"
    assert shipment["sender_id"] == "sender-001"
    assert shipment["courier_id"] == "courier-001"
    assert shipment["proof_of_delivery"] == "receiver-confirmed"


def test_africonnecttl_build_operation_is_kernel_callable_shape():
    operation = build_operation(
        "shipment_assign",
        {
            "shipment_id": "shipment-002",
            "courier_id": "courier-002",
        },
    )

    result = operation(None)

    assert operation.__name__ == "shipment_assign"
    assert result["contract_id"] == "shipment_assign"
    assert result["shipment_id"] == "shipment-002"
    assert result["status"] == "ASSIGNED"
