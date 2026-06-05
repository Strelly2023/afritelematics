from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

from afritech.runtime.kernel.execute import ExecutionContext
from afritech.services.africonnecttl.models import ShipmentStatus


AFRICONNECTTL_FN_IDS = (
    "shipment_request",
    "shipment_assign",
    "shipment_pickup",
    "shipment_transit",
    "shipment_delivered",
)


def build_operation(
    fn_id: str,
    payload: Mapping[str, Any],
) -> Callable[[ExecutionContext], dict[str, Any]]:
    if fn_id not in AFRICONNECTTL_FN_IDS:
        raise ValueError(f"Unsupported AfriConnectTL fn_id: {fn_id}")

    frozen_payload = deepcopy(dict(payload))

    def operation(context: ExecutionContext) -> dict[str, Any]:
        return execute_operation(fn_id, context, frozen_payload)

    operation.__name__ = fn_id
    operation.__qualname__ = fn_id
    return operation


def execute_operation(
    fn_id: str,
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if fn_id == "shipment_request":
        return shipment_request(context, payload)
    if fn_id == "shipment_assign":
        return shipment_assign(context, payload)
    if fn_id == "shipment_pickup":
        return shipment_pickup(context, payload)
    if fn_id == "shipment_transit":
        return shipment_transit(context, payload)
    if fn_id == "shipment_delivered":
        return shipment_delivered(context, payload)
    raise ValueError(f"Unsupported AfriConnectTL fn_id: {fn_id}")


def shipment_request(
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    shipment_id = _required(payload, "shipment_id")
    return {
        "surface": "africonnecttl",
        "contract_id": "shipment_request",
        "shipment_id": shipment_id,
        "sender_id": _required(payload, "sender_id"),
        "receiver_id": _required(payload, "receiver_id"),
        "origin": _required(payload, "origin"),
        "destination": _required(payload, "destination"),
        "status": ShipmentStatus.REQUESTED.value,
    }


def shipment_assign(
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _transition(
        payload,
        contract_id="shipment_assign",
        status=ShipmentStatus.ASSIGNED,
        extra={"courier_id": _required(payload, "courier_id")},
    )


def shipment_pickup(
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _transition(
        payload,
        contract_id="shipment_pickup",
        status=ShipmentStatus.PICKED_UP,
        extra={"courier_id": _optional(payload, "courier_id")},
    )


def shipment_transit(
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _transition(
        payload,
        contract_id="shipment_transit",
        status=ShipmentStatus.IN_TRANSIT,
        extra={"location": _optional(payload, "location")},
    )


def shipment_delivered(
    context: ExecutionContext | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _transition(
        payload,
        contract_id="shipment_delivered",
        status=ShipmentStatus.DELIVERED,
        extra={
            "proof_of_delivery": _required(payload, "proof_of_delivery"),
            "receiver_id": _optional(payload, "receiver_id"),
        },
    )


def _transition(
    payload: Mapping[str, Any],
    *,
    contract_id: str,
    status: ShipmentStatus,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "surface": "africonnecttl",
        "contract_id": contract_id,
        "shipment_id": _required(payload, "shipment_id"),
        "status": status.value,
    }

    for key, value in dict(extra or {}).items():
        if value is not None:
            result[key] = value

    return result


def _required(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string when provided")
    return value
