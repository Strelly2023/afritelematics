"""Ride persistence repository."""

from __future__ import annotations

import json

from afriride_system.backend.state import RideSession
from afriride_system.backend.storage import AfriRideStorage, decode_json_value


class RideRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def save(self, ride: RideSession) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """
                INSERT INTO rides (
                    ride_id,
                    passenger_id,
                    pickup,
                    destination,
                    status,
                    assigned_driver,
                    trace_hash,
                    state_hash,
                    events_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ride_id) DO UPDATE SET
                    passenger_id = excluded.passenger_id,
                    pickup = excluded.pickup,
                    destination = excluded.destination,
                    status = excluded.status,
                    assigned_driver = excluded.assigned_driver,
                    trace_hash = excluded.trace_hash,
                    state_hash = excluded.state_hash,
                    events_json = excluded.events_json
                """,
                (
                    ride.ride_id,
                    ride.passenger_id,
                    ride.pickup,
                    ride.destination,
                    ride.status,
                    ride.assigned_driver,
                    ride.trace_hash,
                    ride.state_hash,
                    json.dumps(list(ride.events)),
                ),
            )

    def get(self, ride_id: str) -> RideSession | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                """
                SELECT ride_id, passenger_id, pickup, destination, status,
                       assigned_driver, trace_hash, state_hash, events_json
                FROM rides
                WHERE ride_id = ?
                """,
                (ride_id,),
            ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def all(self) -> tuple[RideSession, ...]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                """
                SELECT ride_id, passenger_id, pickup, destination, status,
                       assigned_driver, trace_hash, state_hash, events_json
                FROM rides
                ORDER BY ride_id
                """
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def _from_row(self, row) -> RideSession:
        return RideSession(
            ride_id=str(row["ride_id"]),
            passenger_id=str(row["passenger_id"]),
            pickup=str(row["pickup"]),
            destination=str(row["destination"]),
            status=str(row["status"]),
            assigned_driver=row["assigned_driver"],
            trace_hash=row["trace_hash"],
            state_hash=row["state_hash"],
            events=tuple(decode_json_value(row["events_json"])),
        )
