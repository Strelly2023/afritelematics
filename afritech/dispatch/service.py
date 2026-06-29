from __future__ import annotations

from typing import Any

from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.dispatch.matching import select_driver_for_ride
from afritech.dispatch.presence import get_driver_presence, list_driver_presence, set_driver_online


def _store():
    return phase0_control_plane._STORE


def dispatch_ride(
    *,
    organization_id: str,
    ride: dict[str, Any],
    excluded_driver_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    current_presence_by_driver = {
        presence["driver_id"]: presence
        for presence in list_driver_presence(organization_id=organization_id)
    }
    decision = select_driver_for_ride(
        ride=ride,
        driver_presence=list(current_presence_by_driver.values()),
        excluded_driver_ids=excluded_driver_ids,
    )
    if decision is None:
        return None
    selected_driver_id = decision["selected_driver_id"]
    selected_presence = current_presence_by_driver.get(selected_driver_id) or {}
    assigned_ride = _store().update_ride(
        ride_id=ride["ride_id"],
        organization_id=organization_id,
        status="matched",
        driver_id=selected_driver_id,
    )
    assignment = _store().store_dispatch_assignment(
        organization_id=organization_id,
        ride_id=ride["ride_id"],
        driver_id=selected_driver_id,
        status="assigned",
        decision=decision["decision"],
    )
    presence = _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=selected_driver_id,
        status="busy",
        location=selected_presence.get("location") or {},
        busy_ride_id=ride["ride_id"],
        trust_score=float(selected_presence.get("trust_score", 0.0)),
        metadata={"dispatch": decision["decision"]},
    )
    return {
        "ride": assigned_ride,
        "assignment": assignment,
        "driver_presence": presence,
        "decision": decision,
    }


def release_driver(
    *,
    organization_id: str,
    driver_id: str,
    status: str = "online",
    busy_ride_id: str | None = None,
) -> dict[str, Any]:
    presence = get_driver_presence(organization_id=organization_id, driver_id=driver_id) or {}
    return _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status=status,
        location=presence.get("location") or {},
        busy_ride_id=busy_ride_id,
        trust_score=float(presence.get("trust_score", 0.0)),
        metadata=presence.get("metadata") or {},
    )
