"""Live fleet digital twin and proactive trust-aware safety evaluation."""

from __future__ import annotations

from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any


class TrustSafetyEngine:
    def evaluate(self, current: dict[str, Any], previous: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []
        self._add(signals, current.get("is_mocked") is True, "gps_spoofing", "critical", "driver_verification")
        if previous:
            elapsed = max(
                0.001,
                (
                    datetime.fromisoformat(str(current["captured_at"]).replace("Z", "+00:00"))
                    - datetime.fromisoformat(str(previous["captured_at"]).replace("Z", "+00:00"))
                ).total_seconds(),
            )
            implied_kph = (
                _distance_km(
                    float(previous["latitude"]), float(previous["longitude"]),
                    float(current["latitude"]), float(current["longitude"]),
                ) / (elapsed / 3600)
            )
            self._add(signals, implied_kph > 200, "gps_spoofing", "critical", "driver_verification",
                      {"implied_speed_kph": round(implied_kph, 2)})
        speed_kph = float(current.get("speed_mps") or 0) * 3.6
        self._add(signals, speed_kph > 130, "unsafe_speed", "critical", "operations_alert",
                  {"speed_kph": round(speed_kph, 2)})
        self._add(signals, int(current.get("stationary_seconds") or 0) >= 600,
                  "long_stop", "warning", "driver_verification")
        self._add(signals, float(current.get("route_deviation_m") or 0) >= 500,
                  "unexpected_route_deviation", "critical", "rider_verification")
        self._add(signals, not bool(current.get("device_trusted", True)),
                  "device_integrity", "critical", "driver_verification")
        accuracy = current.get("accuracy_m")
        self._add(signals, accuracy is not None and float(accuracy) > 100,
                  "gps_accuracy_degraded", "warning", "operations_alert")
        return signals

    @staticmethod
    def _add(signals, condition, signal_type, severity, workflow, evidence=None):
        if condition:
            signals.append({
                "type": signal_type,
                "severity": severity,
                "workflow": workflow,
                "evidence": evidence or {},
            })


def build_fleet_twin(gateway) -> dict[str, Any]:
    telemetry = list(gateway.fleet_operations_repository.telemetry())
    rides = list(gateway.dispatcher.rides.values())
    drivers = gateway.dispatcher.drivers
    open_incidents = gateway.fleet_operations_repository.incidents("open")
    active_rides = [
        ride.snapshot() for ride in rides
        if ride.status not in {"COMPLETED", "CANCELED"}
    ]
    zones: dict[str, dict[str, Any]] = {}
    positions = []
    for row in telemetry:
        zone = f"{round(float(row['latitude']), 2)}:{round(float(row['longitude']), 2)}"
        bucket = zones.setdefault(zone, {"zone_id": zone, "drivers": 0, "demand": 0})
        bucket["drivers"] += 1
        positions.append({
            "driver_id": row["driver_id"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "heading": row["heading"],
            "speed_kph": round(float(row["speed_mps"] or 0) * 3.6, 2),
            "battery_level": row["battery_level"],
            "device_trusted": bool(row["device_trusted"]),
            "captured_at": row["captured_at"],
        })
    unassigned = sum(ride.status == "REQUESTED" for ride in rides)
    zone_rows = list(zones.values())
    for index in range(unassigned):
        if zone_rows:
            zone_rows[index % len(zone_rows)]["demand"] += 1
    for zone in zone_rows:
        supply = max(1, zone["drivers"])
        zone["pressure"] = round(zone["demand"] / supply, 3)
        zone["surge"] = zone["pressure"] >= 1.5
        zone["traffic"] = _traffic_for_zone(zone["zone_id"], telemetry)
        zone["heat"] = min(1.0, round((zone["demand"] * 0.4) + (zone["pressure"] * 0.6), 3))
    stale = sum(_age_seconds(row["captured_at"]) > 45 for row in telemetry)
    online = sum(driver.online for driver in drivers.values())
    health_score = max(0, round(100 - stale * 5 - len(open_incidents) * 8 - unassigned * 2))
    return {
        "contract": "afriride.fleet_twin.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "driver_positions": positions,
        "active_rides": active_rides,
        "surge_zones": [zone for zone in zone_rows if zone["surge"]],
        "traffic": [{"zone_id": zone["zone_id"], "level": zone["traffic"]} for zone in zone_rows],
        "heat_map": zone_rows,
        "safety_alerts": list(open_incidents),
        "fleet_health": {
            "score": health_score,
            "online_drivers": online,
            "tracked_drivers": len(telemetry),
            "stale_positions": stale,
            "open_incidents": len(open_incidents),
        },
        "queue_lengths": {
            "unassigned_rides": unassigned,
            "active_rides": len(active_rides),
            "push_outbox": len(gateway.push_outbox_repository.pending(1000)),
        },
        "authority": "projection_only",
    }


def _traffic_for_zone(zone_id: str, telemetry: list[dict[str, Any]]) -> str:
    speeds = [
        float(row["speed_mps"] or 0) * 3.6 for row in telemetry
        if f"{round(float(row['latitude']), 2)}:{round(float(row['longitude']), 2)}" == zone_id
    ]
    average = sum(speeds) / len(speeds) if speeds else 0
    return "heavy" if 0 < average < 15 else "moderate" if average < 35 else "light"


def _age_seconds(timestamp: str) -> float:
    captured = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    return max(0, (datetime.now(UTC) - captured).total_seconds())


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))
