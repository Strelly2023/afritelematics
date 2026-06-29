from __future__ import annotations

from typing import Any

from afritech.afriprogramming import control_plane as phase0_control_plane


def _store():
    return phase0_control_plane._STORE


def set_driver_online(
    *,
    organization_id: str,
    driver_id: str,
    location: dict[str, Any] | None = None,
    trust_score: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status="online",
        location=location or {},
        busy_ride_id=None,
        trust_score=trust_score,
        metadata=metadata or {},
    )


def set_driver_offline(
    *,
    organization_id: str,
    driver_id: str,
    location: dict[str, Any] | None = None,
    trust_score: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status="offline",
        location=location or {},
        busy_ride_id=None,
        trust_score=trust_score,
        metadata=metadata or {},
    )


def update_driver_location(
    *,
    organization_id: str,
    driver_id: str,
    location: dict[str, Any],
    status: str | None = None,
    busy_ride_id: str | None = None,
    trust_score: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = get_driver_presence(organization_id=organization_id, driver_id=driver_id) or {}
    return _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status=status or str(current.get("status") or "online"),
        location=location,
        busy_ride_id=busy_ride_id if busy_ride_id is not None else current.get("busy_ride_id"),
        trust_score=current.get("trust_score", 0.0) if trust_score is None else trust_score,
        metadata=metadata or current.get("metadata") or {},
    )


def get_driver_presence(*, organization_id: str, driver_id: str) -> dict[str, Any] | None:
    return _store().get_driver_presence(organization_id=organization_id, driver_id=driver_id)


def list_driver_presence(
    *,
    organization_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _store().list_driver_presence(organization_id=organization_id, status=status, limit=limit)
