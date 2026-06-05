from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def shipment_reducer(
    state: Mapping[str, Any],
    event: Mapping[str, Any],
) -> dict[str, Any]:
    shipment_id = event.get("shipment_id")
    status = event.get("status")

    if not isinstance(shipment_id, str) or not shipment_id:
        raise ValueError("shipment_id is required for shipment state projection")
    if not isinstance(status, str) or not status:
        raise ValueError("status is required for shipment state projection")

    next_state = deepcopy(dict(state))
    shipments = dict(next_state.get("shipments", {}))
    current = dict(shipments.get(shipment_id, {}))

    for key, value in event.items():
        if key in {"surface", "contract_id"}:
            continue
        if value is not None:
            current[key] = value

    shipments[shipment_id] = current
    next_state["shipments"] = shipments
    return next_state
