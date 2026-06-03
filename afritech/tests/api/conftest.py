"""API contract fixtures for AfriRide evidence surfaces.

This fixture provides a bounded in-test FastAPI surface for
contract verification.

It is not production authority.
It exists only to prove that expected API response shapes are
available to contract tests.

The fixture supports:
- completed ride receipt evidence
- completed ride replay evidence
- completed ride price explanation
- assigned driver ride visibility
- driver accept/start/complete action requests
- driver earnings evidence

It does not expose:
- driver-side pricing authority
- driver-side dispatch authority
- replay mutation
- receipt generation authority
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


DRIVER_ID = "driver-1"
ASSIGNED_RIDE_ID = "ride-1"


@pytest.fixture
def completed_ride_id() -> str:
    return "ride.completed.contract.001"


@pytest.fixture
def client(completed_ride_id: str) -> TestClient:
    app = FastAPI(title="AfriRide Contract Test API")

    @app.get("/ride/{ride_id}/receipt")
    def get_receipt(ride_id: str) -> dict[str, str]:
        if ride_id == completed_ride_id:
            return {
                "ride_id": ride_id,
                "receipt_id": "receipt.contract.001",
                "status": "completed",
                "replay_id": "replay.contract.001",
                "receipt_hash": "receipt.hash.contract.001",
                "issued_at": "2026-05-31T00:00:00Z",
            }

        if ride_id == ASSIGNED_RIDE_ID:
            return {
                "ride_id": ride_id,
                "receipt_id": "receipt-1",
                "status": "completed",
                "replay_id": "replay-1",
                "receipt_hash": "receipt-hash-1",
                "issued_at": "2026-05-31T00:00:00Z",
            }

        raise HTTPException(status_code=404, detail="ride not found")

    @app.get("/ride/{ride_id}/replay")
    def get_replay(ride_id: str) -> dict[str, str | bool | int]:
        if ride_id == completed_ride_id:
            return {
                "ride_id": ride_id,
                "replay_id": "replay.contract.001",
                "replay_verified": True,
                "replay_hash": "replay.hash.contract.001",
                "receipt_id": "receipt.contract.001",
                "replay_epoch": 1,
            }

        if ride_id == ASSIGNED_RIDE_ID:
            return {
                "ride_id": ride_id,
                "replay_id": "replay-1",
                "replay_verified": True,
                "replay_hash": "replay-hash-1",
                "receipt_id": "receipt-1",
                "replay_epoch": 1,
            }

        raise HTTPException(status_code=404, detail="ride not found")

    @app.get("/ride/{ride_id}/price-explanation")
    def get_price_explanation(ride_id: str) -> dict[str, str]:
        if ride_id not in {completed_ride_id, ASSIGNED_RIDE_ID}:
            raise HTTPException(status_code=404, detail="ride not found")

        return {
            "ride_id": ride_id,
            "price_explanation": "Deterministic fare returned by core system.",
            "source": "core_system",
        }

    @app.get("/driver/{driver_id}/rides/assigned")
    def get_assigned_rides(driver_id: str) -> dict[str, list[dict[str, str]]]:
        if driver_id != DRIVER_ID:
            return {"rides": []}

        return {
            "rides": [
                {
                    "ride_id": ASSIGNED_RIDE_ID,
                    "pickup": "Pickup A",
                    "dropoff": "Dropoff B",
                    "status": "assigned",
                    "assigned_driver_id": DRIVER_ID,
                    "receipt_id": "receipt-1",
                    "replay_id": "replay-1",
                }
            ]
        }

    @app.post("/ride/{ride_id}/accept", response_model=None)
    def accept_ride(ride_id: str, body: dict[str, Any]):
        return _driver_action_response(
            ride_id=ride_id,
            body=body,
            action="accept",
        )

    @app.post("/ride/{ride_id}/start", response_model=None)
    def start_ride(ride_id: str, body: dict[str, Any]):
        return _driver_action_response(
            ride_id=ride_id,
            body=body,
            action="start",
        )

    @app.post("/ride/{ride_id}/complete", response_model=None)
    def complete_ride(ride_id: str, body: dict[str, Any]):
        return _driver_action_response(
            ride_id=ride_id,
            body=body,
            action="complete",
        )

    @app.get("/driver/{driver_id}/earnings")
    def get_driver_earnings(driver_id: str) -> dict[str, str | float | bool]:
        if driver_id != DRIVER_ID:
            raise HTTPException(status_code=404, detail="driver not found")

        return {
            "driver_id": driver_id,
            "daily_total": 125.50,
            "weekly_total": 650.75,
            "earnings_receipt_id": "earnings-receipt-1",
            "earnings_period_id": "week-2026-22",
            "replay_verified": True,
        }

    return TestClient(app)


def _driver_action_response(
    *,
    ride_id: str,
    body: dict[str, Any],
    action: str,
) -> Any:
    driver_id = body.get("driver_id")

    if ride_id != ASSIGNED_RIDE_ID:
        raise HTTPException(status_code=404, detail="ride not found")

    if driver_id != DRIVER_ID:
        return JSONResponse(
            status_code=409,
            content={"error": "driver_assignment_mismatch"},
        )

    return {
        "ok": True,
        "ride_id": ride_id,
        "driver_id": driver_id,
        "action": action,
    }