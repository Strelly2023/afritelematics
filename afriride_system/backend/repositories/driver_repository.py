"""Driver persistence repository."""

from __future__ import annotations

from afriride_system.backend.state import DriverSession
from afriride_system.backend.storage import AfriRideStorage


class DriverRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def save(self, session: DriverSession) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """
                INSERT INTO drivers (driver_id, online)
                VALUES (?, ?)
                ON CONFLICT(driver_id) DO UPDATE SET online = excluded.online
                """,
                (session.driver_id, int(session.online)),
            )

    def get(self, driver_id: str) -> DriverSession | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT driver_id, online FROM drivers WHERE driver_id = ?",
                (driver_id,),
            ).fetchone()
        if row is None:
            return None
        return DriverSession(driver_id=str(row["driver_id"]), online=bool(row["online"]))

    def all(self) -> tuple[DriverSession, ...]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                "SELECT driver_id, online FROM drivers ORDER BY driver_id"
            ).fetchall()
        return tuple(
            DriverSession(driver_id=str(row["driver_id"]), online=bool(row["online"]))
            for row in rows
        )
