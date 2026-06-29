from __future__ import annotations

from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch


DISPATCH_STALE_DRIVER_THRESHOLD_SECONDS = 180
DISPATCH_BUSY_LOAD_PENALTY = 35.0
DISPATCH_STALE_PENALTY = 40.0
DISPATCH_FRESHNESS_WEIGHT = 28.0
DISPATCH_IDLE_BONUS = 12.0


def _to_location(payload: dict[str, Any]) -> dict[str, Any]:
    lat = payload.get("lat", payload.get("latitude"))
    lon = payload.get("lng", payload.get("lon", payload.get("longitude")))
    if lat is None or lon is None:
        raise ValueError("location requires lat/lng")
    timestamp = payload.get("timestamp")
    if timestamp is None:
        timestamp = int(datetime.now(tz=timezone.utc).timestamp())
    return {"lat": float(lat), "lon": float(lon), "timestamp": int(timestamp)}


def _now_timestamp() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1 = radians(float(a["lat"]))
    lat2 = radians(float(b["lat"]))
    dlat = lat2 - lat1
    dlon = radians(float(b["lon"]) - float(a["lon"]))
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(hav))


def _presence_last_seen(presence: dict[str, Any], *, default_timestamp: int) -> int:
    raw_last_seen = presence.get("last_seen")
    if raw_last_seen is None:
        metadata = presence.get("metadata") or {}
        if isinstance(metadata, dict):
            raw_last_seen = metadata.get("last_seen")
    if raw_last_seen is None:
        location = presence.get("location") or {}
        if isinstance(location, dict):
            raw_last_seen = location.get("timestamp")
    if raw_last_seen is None:
        return default_timestamp
    try:
        return int(raw_last_seen)
    except (TypeError, ValueError):
        return default_timestamp


def _dispatch_capacity(presence: dict[str, Any]) -> int:
    metadata = presence.get("metadata") or {}
    if isinstance(metadata, dict):
        for key in ("dispatch_capacity", "vehicle_capacity", "capacity"):
            value = metadata.get(key)
            if value is None:
                continue
            try:
                capacity = int(value)
            except (TypeError, ValueError):
                continue
            if capacity > 0:
                return capacity
    return 1


def _freshness_score(age_seconds: int) -> float:
    if age_seconds <= 0:
        return 1.0
    if age_seconds >= DISPATCH_STALE_DRIVER_THRESHOLD_SECONDS:
        return 0.0
    return max(0.0, 1.0 - (age_seconds / DISPATCH_STALE_DRIVER_THRESHOLD_SECONDS))


def _dispatch_reliability_score(*, trust_score: float, freshness_score: float, idle: bool, busy: bool) -> float:
    score = (trust_score * 0.62) + (freshness_score * DISPATCH_FRESHNESS_WEIGHT)
    if idle:
        score += DISPATCH_IDLE_BONUS
    if busy:
        score -= DISPATCH_BUSY_LOAD_PENALTY
    return max(0.0, min(100.0, round(score, 6)))


def _dispatch_anomaly_rate(*, freshness_score: float, busy: bool, distance_km: float) -> float:
    anomaly = (1.0 - freshness_score) * DISPATCH_STALE_PENALTY
    if busy:
        anomaly += DISPATCH_BUSY_LOAD_PENALTY
    anomaly += min(distance_km / 2.0, 25.0)
    return max(0.0, min(100.0, round(anomaly, 6)))


def _build_dispatch_candidate(
    *,
    presence: dict[str, Any],
    pickup_location: dict[str, Any],
    now_ts: int,
) -> DispatchCandidate:
    driver_location = _to_location(presence.get("location") or pickup_location)
    trust_score = float(presence.get("trust_score", 0.0))
    last_seen = _presence_last_seen(presence, default_timestamp=now_ts)
    age_seconds = max(0, now_ts - last_seen)
    freshness_score = _freshness_score(age_seconds)
    distance_km = _haversine_km(driver_location, pickup_location)
    busy = bool(presence.get("busy_ride_id"))
    idle = not busy and str(presence.get("status") or "").lower() == "online"
    reliability_score = _dispatch_reliability_score(
        trust_score=trust_score,
        freshness_score=freshness_score,
        idle=idle,
        busy=busy,
    )
    anomaly_rate = _dispatch_anomaly_rate(
        freshness_score=freshness_score,
        busy=busy,
        distance_km=distance_km,
    )
    metadata = {
        "busy_ride_id": presence.get("busy_ride_id"),
        "dispatch_distance_km": round(distance_km, 6),
        "dispatch_freshness_score": round(freshness_score, 6),
        "dispatch_load": 1 if busy else 0,
        "dispatch_priority": round(reliability_score - anomaly_rate, 6),
        "last_seen": last_seen,
        "last_seen_age_seconds": age_seconds,
        "status": presence.get("status"),
    }
    return DispatchCandidate(
        participant=MobilityParticipant(
            participant_id=str(presence["driver_id"]),
            display_name=str(presence["driver_id"]),
            roles=("driver",),
            verification_status="verified",
            trust_score=trust_score,
        ),
        location=driver_location,
        availability=True,
        reliability_score=reliability_score,
        anomaly_rate=anomaly_rate,
        supported_operations=("ride_dispatch", "ride", "ride_assignment"),
        capacity=_dispatch_capacity(presence),
        metadata=metadata,
    )


def select_driver_for_ride(
    *,
    ride: dict[str, Any],
    driver_presence: list[dict[str, Any]],
    excluded_driver_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    excluded_driver_ids = excluded_driver_ids or set()
    now_ts = _now_timestamp()
    pickup_location = _to_location(ride["pickup_location"])
    destination_location = _to_location(ride["destination_location"])
    eligible = [
        presence
        for presence in driver_presence
        if presence.get("status") == "online"
        and not presence.get("busy_ride_id")
        and presence.get("driver_id") not in excluded_driver_ids
    ]
    if not eligible:
        return None
    request = DispatchRequest.from_mapping(
        {
            "operation_id": ride["ride_id"],
            "operation_type": "ride_dispatch",
            "origin": pickup_location,
            "destination": destination_location,
            "timestamp": now_ts,
        }
    )
    candidates = [
        _build_dispatch_candidate(
            presence=item,
            pickup_location=pickup_location,
            now_ts=now_ts,
        )
        for item in eligible
    ]
    decision = run_trust_aware_dispatch(request, candidates)
    selected = decision.selected_participant_id
    ranked = [candidate.canonical_dict() for candidate in decision.ranked_candidates]
    return {
        "selected_driver_id": selected,
        "decision": decision.canonical_dict(),
        "ranked_candidates": ranked,
        "request": request.canonical_dict(),
    }
