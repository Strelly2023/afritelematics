from __future__ import annotations

import socket
import threading
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app


class HttpClient(Protocol):
    def get(self, url: str, *, headers: dict[str, str] | None = None) -> Any:
        ...

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        ...


@dataclass(frozen=True)
class RiderHarnessClient:
    client: HttpClient

    def _headers(self, rider_id: str, *, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {JWT.create_token(rider_id, 'RIDER')}"}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def request_ride(self, *, ride_id: str, rider_id: str) -> dict[str, Any]:
        response = self.client.post(
            "/passenger/request-ride",
            json={
                "passenger_id": rider_id,
                "pickup": "Kampala Road",
                "destination": "Nakasero",
                "ride_id": ride_id,
            },
            headers=self._headers(rider_id, idempotency_key=f"{ride_id}-rider-request"),
        )
        assert response.status_code == 200
        return response.json()["data"]

    def status(self, ride_id: str, rider_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/passenger/status/{ride_id}",
            headers=self._headers(rider_id),
        )
        assert response.status_code == 200
        return response.json()["data"]

    def receipt(self, ride_id: str, rider_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/receipt",
            headers=self._headers(rider_id),
        )
        assert response.status_code == 200
        return response.json()

    def replay(self, ride_id: str, rider_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/replay",
            headers=self._headers(rider_id),
        )
        assert response.status_code == 200
        return response.json()

    def ledger_receipt(self, ride_id: str, rider_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/ledger-receipt",
            headers=self._headers(rider_id),
        )
        assert response.status_code == 200
        return response.json()


@dataclass(frozen=True)
class DriverHarnessClient:
    client: HttpClient

    def _headers(self, driver_id: str, *, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {JWT.create_token(driver_id, 'DRIVER')}"}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def go_online(self, driver_id: str) -> dict[str, Any]:
        response = self.client.post(
            "/driver/status",
            json={"driver_id": driver_id, "online": True},
            headers=self._headers(driver_id, idempotency_key=f"{driver_id}-live-local-online"),
        )
        assert response.status_code == 200
        return response.json()["data"]

    def assigned_rides(self, driver_id: str) -> list[dict[str, Any]]:
        response = self.client.get(
            f"/driver/{driver_id}/rides/assigned",
            headers=self._headers(driver_id),
        )
        assert response.status_code == 200
        return response.json()["rides"]

    def accept(self, *, ride_id: str, driver_id: str) -> dict[str, Any]:
        return self._ride_action("accept", ride_id=ride_id, driver_id=driver_id)

    def start(self, *, ride_id: str, driver_id: str) -> dict[str, Any]:
        return self._ride_action("start", ride_id=ride_id, driver_id=driver_id)

    def arrive(self, *, ride_id: str, driver_id: str) -> dict[str, Any]:
        return self._ride_action("arrive", ride_id=ride_id, driver_id=driver_id)

    def complete(self, *, ride_id: str, driver_id: str) -> dict[str, Any]:
        return self._ride_action("complete", ride_id=ride_id, driver_id=driver_id)

    def receipt(self, ride_id: str, driver_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/receipt",
            headers=self._headers(driver_id),
        )
        assert response.status_code == 200
        return response.json()

    def replay(self, ride_id: str, driver_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/replay",
            headers=self._headers(driver_id),
        )
        assert response.status_code == 200
        return response.json()

    def ledger_receipt(self, ride_id: str, driver_id: str) -> dict[str, Any]:
        response = self.client.get(
            f"/ride/{ride_id}/ledger-receipt",
            headers=self._headers(driver_id),
        )
        assert response.status_code == 200
        return response.json()

    def _ride_action(
        self,
        action: str,
        *,
        ride_id: str,
        driver_id: str,
    ) -> dict[str, Any]:
        response = self.client.post(
            f"/ride/{ride_id}/{action}",
            json={"driver_id": driver_id},
            headers=self._headers(driver_id, idempotency_key=f"{ride_id}-{driver_id}-{action}"),
        )
        assert response.status_code == 200
        return response.json()


def test_live_local_rider_backend_driver_clients_share_same_proof_surface() -> None:
    reset_gateway()
    rider = RiderHarnessClient(TestClient(app))
    driver = DriverHarnessClient(TestClient(app))

    _assert_rider_driver_shared_proof_lifecycle(
        rider=rider,
        driver=driver,
        ride_id="ride-live-local-e2e-1",
        rider_id="rider-live-local-1",
        driver_id="driver-1",
    )


def test_running_backend_rider_and_driver_clients_share_same_proof_surface() -> None:
    with RunningBackend() as base_url:
        with httpx.Client(base_url=base_url, timeout=5.0) as rider_http:
            with httpx.Client(base_url=base_url, timeout=5.0) as driver_http:
                _assert_rider_driver_shared_proof_lifecycle(
                    rider=RiderHarnessClient(rider_http),
                    driver=DriverHarnessClient(driver_http),
                    ride_id="ride-running-backend-e2e-1",
                    rider_id="rider-running-backend-1",
                    driver_id="driver-1",
                )


class RunningBackend(AbstractContextManager[str]):
    def __enter__(self) -> str:
        reset_gateway()
        self.port = _free_port()
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="error",
            lifespan="off",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._wait_until_ready()
        return self.base_url

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"{self.base_url}/", timeout=0.2)
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.05)
        raise RuntimeError("local AfriRide backend did not start")


def _assert_rider_driver_shared_proof_lifecycle(
    *,
    rider: RiderHarnessClient,
    driver: DriverHarnessClient,
    ride_id: str,
    rider_id: str,
    driver_id: str,
) -> None:
    driver_online = driver.go_online(driver_id)
    requested = rider.request_ride(ride_id=ride_id, rider_id=rider_id)
    assigned = driver.assigned_rides(driver_id)

    assert driver_online["driver_id"] == driver_id
    assert requested["ride_id"] == ride_id
    assert assigned == [
        {
            "ride_id": ride_id,
            "pickup": "Kampala Road",
            "dropoff": "Nakasero",
            "status": "assigned",
            "assigned_driver_id": driver_id,
            "receipt_id": None,
            "replay_id": None,
        }
    ]

    accepted = driver.accept(ride_id=ride_id, driver_id=driver_id)
    arrived = driver.arrive(ride_id=ride_id, driver_id=driver_id)
    started = driver.start(ride_id=ride_id, driver_id=driver_id)
    completed = driver.complete(ride_id=ride_id, driver_id=driver_id)
    rider_status = rider.status(ride_id, rider_id)

    assert accepted["status"] == "DRIVER_ASSIGNED"
    assert arrived["status"] == "DRIVER_ARRIVED"
    assert started["status"] == "IN_TRIP"
    assert completed["status"] == "COMPLETED"
    assert rider_status["status"] == "COMPLETED"
    assert rider_status["assigned_driver"] == driver_id

    rider_receipt = rider.receipt(ride_id, rider_id)
    driver_receipt = driver.receipt(ride_id, driver_id)
    rider_replay = rider.replay(ride_id, rider_id)
    driver_replay = driver.replay(ride_id, driver_id)
    rider_ledger = rider.ledger_receipt(ride_id, rider_id)
    driver_ledger = driver.ledger_receipt(ride_id, driver_id)

    assert rider_receipt == driver_receipt
    assert rider_replay == driver_replay
    assert rider_ledger["receipt_hash"] == driver_ledger["receipt_hash"]
    assert rider_ledger["ledger_proof"] == driver_ledger["ledger_proof"]
    assert rider_ledger["signature_validation"] == driver_ledger["signature_validation"]
    assert rider_ledger["identity_validation"] == driver_ledger["identity_validation"]

    assert rider_ledger["verdict"] == "VALID"
    assert rider_ledger["ledger_proof"]["event_count"] == 8
    assert rider_ledger["ledger_proof"]["hash_mode"] == "sha256_canonical_chain"
    assert rider_ledger["signature_validation"]["signature_mode"] == "rsa_pss_sha256"
    assert rider_ledger["signature_validation"]["all_signatures_valid"] is True
    assert rider_ledger["identity_validation"]["all_verified"] is True
    assert rider_ledger["replay_proof"]["replay_valid"] is True
    assert rider_ledger["write_enabled"] is False
    assert rider_ledger["authority"] == "derived_evidence_only"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
        except PermissionError as exc:
            pytest.skip(f"local port binding not permitted in this environment: {exc}")
        return int(sock.getsockname()[1])
