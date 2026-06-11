from __future__ import annotations

import pytest
from typing import Any, Dict

from django.test import Client as DjangoClient
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from afritech.api import afriride_driver_views
from afritech.api.afriride_driver_views import driver_status
from afritech.models import EventRecord
from afritech.proof.contract_snapshot_receipt import build_driver_api_contract_receipt
from afritech.trust_kernel.events import process_command as real_process_command
from afritech.trust_kernel.policy import Command
from afritech.trust_kernel.replay.contract_bindings import (
    ContractBindingReplayError,
    validate_driver_event_contract_binding,
)


def get_response_data(response: Any) -> Dict[str, Any]:
    if isinstance(response, Response):
        data = response.data
    else:
        data = response.json()

    if not isinstance(data, dict):
        raise AssertionError(f"Expected dict response, got {type(data).__name__}")

    return data


def build_contract_binding() -> tuple[Any, dict[str, Any]]:
    receipt = build_driver_api_contract_receipt()
    return receipt, {
        "contract": receipt.contract,
        "version": receipt.version,
        "snapshot_hash": receipt.snapshot_hash,
        "contract_receipt_hash": receipt.receipt_hash,
        "event_hash": receipt.event_hash,
    }


def seed_driver_lifecycle_until_started(
    *,
    ride_id: str,
    driver_id: str = "D001",
    contract_binding: dict[str, Any],
) -> None:
    afriride_driver_views._RIDES.pop(ride_id, None)

    for event_type, status in [
        ("RideAccepted", "accepted"),
        ("RideArrived", "arrived"),
        ("RideStarted", "started"),
    ]:
        real_process_command(
            Command(
                event_type=event_type,
                actor_id=driver_id,
                subject_id=ride_id,
                payload={
                    "ride_id": ride_id,
                    "status": status,
                    "contract_binding": contract_binding,
                },
                signature={"signature_mode": "development_adapter"},
            )
        )

    afriride_driver_views._RIDES[ride_id] = {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "rider_name": "Demo Rider",
        "pickup_text": "Bujumbura Central",
        "dropoff_text": "Rohero Market",
        "quoted_total_text": "BIF 5,000",
        "status": "started",
        "contract_binding": contract_binding,
    }


def test_driver_status_accepts_online_status_without_mutating_request():
    request = APIRequestFactory().post(
        "/driver/status",
        {"driver_id": "D001", "status": "online"},
        format="json",
    )
    response = driver_status(request)

    data = get_response_data(response)

    assert response.status_code == 200
    assert data["driver_id"] == "D001"
    assert data["status"] == "available"


def test_driver_status_rejects_unknown_status():
    request = APIRequestFactory().post(
        "/driver/status",
        {"driver_id": "D001", "status": "busy"},
        format="json",
    )
    response = driver_status(request)

    data = get_response_data(response)

    assert response.status_code == 400
    assert "status must be" in data["detail"]


def test_driver_availability_post_is_valid_on_root_driver_route():
    response = DjangoClient().post(
        "/driver/availability",
        data={"driver_id": "D001", "status": "available"},
        content_type="application/json",
    )

    data = get_response_data(response)

    assert response.status_code == 200
    assert data["status"] == "available"


def test_driver_availability_post_is_valid_on_declared_api_prefix():
    response = DjangoClient().post(
        "/api/driver/availability",
        data={"driver_id": "D001", "status": "available"},
        content_type="application/json",
    )

    data = get_response_data(response)

    assert response.status_code == 200
    assert data["status"] == "available"


def test_driver_availability_get_is_method_rejected_not_silent_write():
    response = DjangoClient().get("/driver/availability")

    assert response.status_code == 405


def test_driver_availability_trailing_slash_is_not_implicit_alias():
    response = DjangoClient().post(
        "/api/driver/availability/",
        data={"driver_id": "D001", "status": "available"},
        content_type="application/json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_driver_lifecycle_events_include_contract_receipt_binding(monkeypatch):
    captured: list[Command] = []

    def fake_process_command(command: Command):
        captured.append(command)
        return real_process_command(command)

    client = DjangoClient()
    receipt, contract_binding = build_contract_binding()

    seed_driver_lifecycle_until_started(
        ride_id="ride-demo-contract-binding",
        contract_binding=contract_binding,
    )

    monkeypatch.setattr(
        afriride_driver_views,
        "process_command",
        fake_process_command,
    )

    response = client.post(
        "/ride/ride-demo-contract-binding/complete",
        data={"driver_id": "D001"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert captured

    binding = captured[-1].payload["contract_binding"]

    assert binding["snapshot_hash"] == receipt.snapshot_hash
    assert binding["contract_receipt_hash"] == receipt.receipt_hash
    assert binding["event_hash"] == receipt.event_hash


@pytest.mark.django_db
def test_driver_replay_history_reports_contract_receipt_binding():
    ride_id = "ride-demo-replay-contract"

    receipt, contract_binding = build_contract_binding()

    seed_driver_lifecycle_until_started(
        ride_id=ride_id,
        contract_binding=contract_binding,
    )

    response = DjangoClient().post(
        f"/ride/{ride_id}/complete",
        data={"driver_id": "D001"},
        content_type="application/json",
    )

    history = DjangoClient().get("/driver/replay-history?driver_id=D001")

    assert response.status_code == 200
    assert history.status_code == 200

    replayed = [
        ride
        for ride in history.json()["rides"]
        if ride["ride_id"] == ride_id
    ][-1]["contract_replay"]

    assert replayed["replay_verified"] is True
    assert replayed["snapshot_hash"] == receipt.snapshot_hash
    assert replayed["contract_receipt_hash"] == receipt.receipt_hash
    assert replayed["receipt_resolution"] == "timestamp_aligned_indexed_receipt"
    assert replayed["receipt_id"] == "driver_api_routes_v1"
    assert replayed["receipt_effective_from"] == "2026-06-01T00:00:00Z"
    assert replayed["receipt_effective_to"] is None


@pytest.mark.django_db
def test_driver_event_contract_replay_rejects_tampered_binding():
    receipt = build_driver_api_contract_receipt()

    event = real_process_command(
        Command(
            event_type="RideAccepted",
            actor_id="D001",
            subject_id="ride-tampered-contract",
            payload={
                "ride_id": "ride-tampered-contract",
                "status": "accepted",
                "contract_binding": {
                    "contract": receipt.contract,
                    "version": receipt.version,
                    "snapshot_hash": receipt.snapshot_hash,
                    "contract_receipt_hash": "0" * 64,
                    "event_hash": receipt.event_hash,
                },
            },
            signature={"signature_mode": "development_adapter"},
        )
    )

    with pytest.raises(
        ContractBindingReplayError,
        match="event contract receipt cannot resolve from index",
    ):
        validate_driver_event_contract_binding(
            EventRecord.objects.get(event_id=event.event_id)
        )
