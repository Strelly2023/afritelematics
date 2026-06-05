from __future__ import annotations

from afritech.ci.africonnecttl_phase2_validator import validate
from afritech.services.africonnecttl.execution import execute_operation
from afritech.services.africonnecttl.registry import (
    EVIDENCE_FIELDS,
    SHIPMENT_LIFECYCLE,
    STOP_CONDITIONS,
    STATE_REDUCERS,
    SURFACE_DEFINITION,
    validate_lifecycle,
    validate_surface_contract,
)


def test_africonnecttl_phase2_validator_passes():
    assert validate() is True


def test_africonnecttl_surface_registry_is_planned_replay_only():
    assert validate_surface_contract() is True
    assert SURFACE_DEFINITION == {
        "surface": "africonnecttl",
        "domain": "logistics",
        "type": "execution_surface",
        "authority": "replay_only",
        "status": "PLANNED",
        "live_deployment": "FORBIDDEN",
        "truth_source": "replay_receipts_only",
    }
    assert "africonnecttl.shipment" in STATE_REDUCERS


def test_africonnecttl_lifecycle_order_is_enforced():
    events = [
        execute_operation(
            "shipment_request",
            None,
            {
                "shipment_id": "shipment-phase2-001",
                "sender_id": "sender-001",
                "receiver_id": "receiver-001",
                "origin": "Kampala",
                "destination": "Jinja",
            },
        ),
        execute_operation(
            "shipment_assign",
            None,
            {
                "shipment_id": "shipment-phase2-001",
                "courier_id": "courier-001",
            },
        ),
        execute_operation(
            "shipment_pickup",
            None,
            {
                "shipment_id": "shipment-phase2-001",
                "courier_id": "courier-001",
            },
        ),
        execute_operation(
            "shipment_transit",
            None,
            {
                "shipment_id": "shipment-phase2-001",
                "location": "Mukono",
            },
        ),
        execute_operation(
            "shipment_delivered",
            None,
            {
                "shipment_id": "shipment-phase2-001",
                "proof_of_delivery": "receiver-confirmed",
            },
        ),
    ]

    assert validate_lifecycle(events) is True
    assert tuple((event["contract_id"], event["status"]) for event in events) == (
        SHIPMENT_LIFECYCLE
    )


def test_africonnecttl_evidence_and_stop_conditions_are_locked():
    assert EVIDENCE_FIELDS == (
        "shipment_id",
        "execution_trace",
        "proof_receipts",
        "ledger_block_hash",
        "replay_verification",
        "device_source",
        "timestamps",
    )
    assert STOP_CONDITIONS == (
        "replay_mismatch",
        "missing_transition",
        "wrong_state_ordering",
        "unsigned_proof",
        "inconsistent_ledger",
    )
