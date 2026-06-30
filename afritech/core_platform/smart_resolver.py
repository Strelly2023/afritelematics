"""Deterministic smart resolver for GPS and connectivity loss.

The resolver is intentionally offline-first:
- it never depends on live network calls,
- it can dead-reckon from the last known position,
- it returns a bounded recovery plan that a driver app can cache locally,
- and it separates guidance, safety, and sync behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Any, Mapping
import time


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalize_location(location: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _safe_mapping(location)
    lat = payload.get("lat", payload.get("latitude"))
    lon = payload.get("lng", payload.get("lon", payload.get("longitude")))
    normalized = {
        "lat": None if lat is None else round(_safe_float(lat), 6),
        "lon": None if lon is None else round(_safe_float(lon), 6),
        "heading_deg": None if payload.get("heading_deg") is None else round(_safe_float(payload.get("heading_deg")), 2),
        "speed_kph": None if payload.get("speed_kph") is None else round(max(0.0, _safe_float(payload.get("speed_kph"))), 2),
        "timestamp": payload.get("timestamp"),
        "label": None if payload.get("label") is None else str(payload.get("label")),
        "source": None if payload.get("source") is None else str(payload.get("source")),
        "accuracy_m": None if payload.get("accuracy_m") is None else round(max(0.0, _safe_float(payload.get("accuracy_m"))), 2),
    }
    if normalized["lon"] is None and payload.get("lng") is None and payload.get("longitude") is None:
        normalized["lon"] = None
    return normalized


def _normalize_connectivity(connectivity: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _safe_mapping(connectivity)
    gps = bool(payload.get("gps", payload.get("gps_available", True)))
    network = bool(payload.get("network", payload.get("network_available", True)))
    internet = bool(payload.get("internet", payload.get("internet_available", True)))
    cached_route = bool(payload.get("cached_route", payload.get("route_cache_available", False)))
    return {
        "gps": gps,
        "network": network,
        "internet": internet,
        "cached_route": cached_route,
    }


def _waypoints(route_context: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    payload = _safe_mapping(route_context)
    waypoints = payload.get("waypoints") or payload.get("route") or payload.get("cached_route") or []
    if not isinstance(waypoints, list):
        return []
    normalized: list[dict[str, Any]] = []
    for waypoint in waypoints:
        if isinstance(waypoint, Mapping):
            normalized.append(
                {
                    "name": str(waypoint.get("name") or waypoint.get("label") or waypoint.get("id") or "waypoint"),
                    "lat": None if waypoint.get("lat") is None else round(_safe_float(waypoint.get("lat")), 6),
                    "lon": None if waypoint.get("lon", waypoint.get("lng")) is None else round(_safe_float(waypoint.get("lon", waypoint.get("lng"))), 6),
                    "status": str(waypoint.get("status") or "pending"),
                }
            )
        else:
            normalized.append({"name": str(waypoint), "lat": None, "lon": None, "status": "pending"})
    return normalized


def _dead_reckon(location: Mapping[str, Any], *, sample_age_seconds: int) -> dict[str, Any]:
    lat = location.get("lat")
    lon = location.get("lon")
    if lat is None or lon is None:
        return dict(location)

    heading = location.get("heading_deg")
    speed_kph = location.get("speed_kph")
    if heading is None or speed_kph is None or sample_age_seconds <= 0:
        return dict(location)

    distance_m = max(0.0, float(speed_kph)) * 1000.0 * (float(sample_age_seconds) / 3600.0)
    bearing = radians(float(heading))
    lat_rad = radians(float(lat))
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = max(1.0, 111_320.0 * cos(lat_rad))

    dead_reckoned = {
        **location,
        "lat": round(float(lat) + (distance_m * cos(bearing)) / meters_per_degree_lat, 6),
        "lon": round(float(lon) + (distance_m * sin(bearing)) / meters_per_degree_lon, 6),
        "source": "dead_reckoning",
        "distance_m": round(distance_m, 2),
    }
    return dead_reckoned


def _route_progress(waypoints: list[dict[str, Any]], location: Mapping[str, Any]) -> dict[str, Any]:
    if not waypoints:
        return {
            "progress_state": "no_cached_route",
            "current_waypoint": None,
            "next_waypoint": None,
            "remaining_waypoints": [],
        }

    next_waypoint = next((waypoint for waypoint in waypoints if waypoint.get("status") != "reached"), waypoints[0])
    remaining = [waypoint for waypoint in waypoints if waypoint.get("status") != "reached"]
    return {
        "progress_state": "cached_route_available",
        "current_waypoint": waypoints[0],
        "next_waypoint": next_waypoint,
        "remaining_waypoints": remaining,
    }


@dataclass(frozen=True)
class SmartResolverResult:
    mode: str
    action: str
    confidence: float
    connectivity: dict[str, Any]
    location: dict[str, Any]
    route: dict[str, Any]
    safety: dict[str, Any]
    sync: dict[str, Any]
    guidance: str
    resolver_version: str = "smart_resolver.v1"
    evaluated_at: float = 0.0

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "resolver_version": self.resolver_version,
            "evaluated_at": self.evaluated_at,
            "mode": self.mode,
            "action": self.action,
            "confidence": round(float(self.confidence), 4),
            "connectivity": self.connectivity,
            "location": self.location,
            "route": self.route,
            "safety": self.safety,
            "sync": self.sync,
            "guidance": self.guidance,
        }


class SmartResolver:
    """Offline-first resolver for GPS loss and connectivity outages."""

    def resolve(
        self,
        *,
        ride_id: str,
        driver_id: str,
        location: Mapping[str, Any] | None = None,
        route_context: Mapping[str, Any] | None = None,
        connectivity: Mapping[str, Any] | None = None,
        telemetry: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        location_payload = _normalize_location(location)
        connectivity_payload = _normalize_connectivity(connectivity)
        telemetry_payload = _safe_mapping(telemetry)
        waypoints = _waypoints(route_context)
        age_seconds = _safe_int(
            telemetry_payload.get("sample_age_seconds", telemetry_payload.get("age_seconds")),
            0,
        )

        gps_available = connectivity_payload["gps"]
        network_available = connectivity_payload["network"]
        internet_available = connectivity_payload["internet"]
        fully_connected = gps_available and network_available and internet_available
        fully_disconnected = not gps_available and not network_available and not internet_available

        resolved_location = dict(location_payload)
        if fully_disconnected:
            resolved_location = _dead_reckon(location_payload, sample_age_seconds=age_seconds)
        elif not gps_available and (network_available or internet_available):
            resolved_location["source"] = "network_assisted"

        route = {
            **_route_progress(waypoints, resolved_location),
            "cached_route_available": bool(waypoints or connectivity_payload["cached_route"]),
            "route_context": _safe_mapping(route_context),
        }
        route["route_cache_status"] = "available" if route["cached_route_available"] else "missing"

        if fully_connected:
            mode = "online"
            action = "continue_normal_navigation"
            confidence = 0.99
            guidance = "Proceed normally and keep streaming updates."
            safety = {
                "allow_trip_continue": True,
                "allow_pickup": True,
                "allow_dropoff": True,
                "require_manual_review": False,
            }
            sync = {"strategy": "live_sync", "queue_locally": False, "sync_on_reconnect": False}
        elif gps_available:
            mode = "degraded_connectivity"
            action = "continue_with_cache"
            confidence = 0.82 if network_available or internet_available else 0.74
            guidance = "Use cached route guidance and keep local state ready for reconciliation."
            safety = {
                "allow_trip_continue": True,
                "allow_pickup": True,
                "allow_dropoff": True,
                "require_manual_review": not (network_available or internet_available),
            }
            sync = {"strategy": "queue_local_events", "queue_locally": True, "sync_on_reconnect": True}
        elif waypoints:
            mode = "offline_continuity"
            action = "dead_reckon_and_hold_sync"
            confidence = 0.70 if age_seconds < 300 else 0.58
            guidance = "GPS is unavailable. Follow the cached route, dead-reckon from the last fix, and sync when connectivity returns."
            safety = {
                "allow_trip_continue": True,
                "allow_pickup": False,
                "allow_dropoff": True,
                "require_manual_review": False,
            }
            sync = {"strategy": "queue_local_events", "queue_locally": True, "sync_on_reconnect": True}
        else:
            mode = "offline_handover"
            action = "hold_position_and_request_manual_checkin"
            confidence = 0.52
            guidance = "No GPS and no cached route are available. Hold position and request dispatcher check-in."
            safety = {
                "allow_trip_continue": False,
                "allow_pickup": False,
                "allow_dropoff": False,
                "require_manual_review": True,
            }
            sync = {"strategy": "store_local_event_log", "queue_locally": True, "sync_on_reconnect": True}

        result = SmartResolverResult(
            mode=mode,
            action=action,
            confidence=_clamp(confidence, 0.0, 0.99),
            connectivity={
                **connectivity_payload,
                "fully_connected": fully_connected,
                "fully_disconnected": fully_disconnected,
            },
            location={
                **resolved_location,
                "sample_age_seconds": max(0, age_seconds),
                "last_known_fix": _safe_mapping(location),
            },
            route=route,
            safety=safety,
            sync=sync,
            guidance=guidance,
            evaluated_at=time.time(),
        )
        return result.canonical_dict() | {
            "ride_id": ride_id,
            "driver_id": driver_id,
        }


def resolve_smart_offline_navigation(
    *,
    ride_id: str,
    driver_id: str,
    location: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
    connectivity: Mapping[str, Any] | None = None,
    telemetry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolver = SmartResolver()
    return resolver.resolve(
        ride_id=ride_id,
        driver_id=driver_id,
        location=location,
        route_context=route_context,
        connectivity=connectivity,
        telemetry=telemetry,
    )


__all__ = ["SmartResolver", "SmartResolverResult", "resolve_smart_offline_navigation"]
