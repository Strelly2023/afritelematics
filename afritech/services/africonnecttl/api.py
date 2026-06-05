from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from afritech.services.africonnecttl.execution import execute_operation
from afritech.services.africonnecttl.reducers import shipment_reducer


router = APIRouter(prefix="/shipment", tags=["africonnecttl"])
_STATE: dict[str, Any] = {"shipments": {}}


@router.post("/request")
def request_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return _apply("shipment_request", payload)


@router.post("/assign")
def assign_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return _apply("shipment_assign", payload)


@router.post("/pickup")
def pickup_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return _apply("shipment_pickup", payload)


@router.post("/transit")
def transit_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return _apply("shipment_transit", payload)


@router.post("/deliver")
def deliver_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return _apply("shipment_delivered", payload)


@router.get("/{shipment_id}")
def get_shipment(shipment_id: str) -> dict[str, Any]:
    shipment = _STATE.get("shipments", {}).get(shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {"shipment": shipment}


def _apply(fn_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        event = execute_operation(fn_id, None, payload)
        global _STATE
        _STATE = shipment_reducer(_STATE, event)
        return {
            "status": "accepted",
            "classification": "planned_controlled_surface",
            "event": event,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
