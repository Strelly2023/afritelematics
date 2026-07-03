"""Shared fleet telemetry and safety incident persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from afriride_system.backend.storage import AfriRideStorage, decode_json_value


class FleetOperationsRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def upsert_telemetry(self, payload: dict[str, Any]) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """INSERT INTO driver_telemetry (
                    driver_id, latitude, longitude, heading, speed_mps, accuracy_m,
                    battery_level, device_trusted, is_mocked, route_deviation_m,
                    stationary_seconds, captured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(driver_id) DO UPDATE SET
                    latitude=excluded.latitude, longitude=excluded.longitude,
                    heading=excluded.heading, speed_mps=excluded.speed_mps,
                    accuracy_m=excluded.accuracy_m, battery_level=excluded.battery_level,
                    device_trusted=excluded.device_trusted, is_mocked=excluded.is_mocked,
                    route_deviation_m=excluded.route_deviation_m,
                    stationary_seconds=excluded.stationary_seconds,
                    captured_at=excluded.captured_at""",
                (
                    payload["driver_id"], payload["latitude"], payload["longitude"],
                    payload.get("heading"), payload.get("speed_mps"), payload.get("accuracy_m"),
                    payload.get("battery_level"), int(payload.get("device_trusted", True)),
                    int(payload.get("is_mocked", False)), payload.get("route_deviation_m"),
                    int(payload.get("stationary_seconds", 0)), payload["captured_at"],
                ),
            )

    def telemetry(self) -> tuple[dict[str, Any], ...]:
        with self.storage.connect() as connection:
            return connection.execute(
                "SELECT * FROM driver_telemetry ORDER BY driver_id"
            ).fetchall()

    def telemetry_for(self, driver_id: str) -> dict[str, Any] | None:
        with self.storage.connect() as connection:
            return connection.execute(
                "SELECT * FROM driver_telemetry WHERE driver_id = ?", (driver_id,)
            ).fetchone()

    def create_incident(self, *, idempotency_key: str, incident_type: str,
                        severity: str, workflow: str, evidence: dict[str, Any],
                        driver_id: str | None = None, rider_id: str | None = None,
                        ride_id: str | None = None) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self.storage.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM safety_incidents WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                return self._incident(existing)
            incident_id = f"incident-{uuid4().hex}"
            connection.execute(
                """INSERT INTO safety_incidents (
                    incident_id, idempotency_key, incident_type, severity, status,
                    driver_id, rider_id, ride_id, workflow, evidence_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)""",
                (incident_id, idempotency_key, incident_type, severity, driver_id,
                 rider_id, ride_id, workflow,
                 json.dumps(evidence, sort_keys=True, separators=(",", ":")), now, now),
            )
            row = connection.execute(
                "SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
        return self._incident(row)

    def incidents(self, status: str | None = None) -> tuple[dict[str, Any], ...]:
        query = "SELECT * FROM safety_incidents"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with self.storage.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return tuple(self._incident(row) for row in rows)

    def transition_incident(self, incident_id: str, action: str) -> dict[str, Any]:
        status_by_action = {
            "acknowledge": "acknowledged",
            "driver_verified": "verified",
            "rider_verified": "verified",
            "sos_dispatched": "responding",
            "resolve": "resolved",
        }
        if action not in status_by_action:
            raise ValueError("invalid_incident_action")
        with self.storage.connect() as connection:
            current = connection.execute(
                "SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
            if not current:
                raise KeyError("incident_not_found")
            if current["status"] == "resolved":
                return self._incident(current)
            connection.execute(
                "UPDATE safety_incidents SET status = ?, updated_at = ? WHERE incident_id = ?",
                (status_by_action[action], datetime.now(UTC).isoformat(), incident_id),
            )
            updated = connection.execute(
                "SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
        return self._incident(updated)

    @staticmethod
    def _incident(row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "evidence": decode_json_value(row["evidence_json"])}
