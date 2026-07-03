"""Durable mobile push outbox repository."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from afriride_system.backend.storage import AfriRideStorage, decode_json_value


class PushOutboxRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def enqueue(self, actor_id: str, event_type: str, payload: dict[str, Any],
                *, idempotency_key: str) -> str:
        with self.storage.connect() as connection:
            return self.enqueue_on(connection, actor_id, event_type, payload,
                                   idempotency_key=idempotency_key)

    def enqueue_on(self, connection, actor_id: str, event_type: str,
                   payload: dict[str, Any], *, idempotency_key: str) -> str:
        existing = connection.execute(
            "SELECT outbox_id FROM mobile_push_outbox WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            return str(existing["outbox_id"])
        outbox_id = f"push-{uuid4().hex}"
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """INSERT INTO mobile_push_outbox (
                outbox_id, idempotency_key, actor_id, event_type, payload_json,
                status, delivery_attempt, next_attempt_at, created_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)""",
            (outbox_id, idempotency_key, actor_id, event_type,
             json.dumps(payload, sort_keys=True, separators=(",", ":")), now, now),
        )
        return outbox_id

    def pending(self, limit: int = 100) -> tuple[dict[str, Any], ...]:
        now = datetime.now(UTC).isoformat()
        with self.storage.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM mobile_push_outbox
                   WHERE status IN ('pending', 'retry') AND next_attempt_at <= ?
                   ORDER BY created_at LIMIT ?""",
                (now, limit),
            ).fetchall()
        return tuple({**row, "payload": decode_json_value(row["payload_json"])} for row in rows)

    def claim_pending(self, limit: int = 100) -> tuple[dict[str, Any], ...]:
        """Atomically claim rows so multiple workers cannot double-deliver."""
        now = datetime.now(UTC).isoformat()
        lease_until = (datetime.now(UTC) + timedelta(seconds=60)).isoformat()
        claimed: list[dict[str, Any]] = []
        with self.storage.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM mobile_push_outbox
                   WHERE ((status IN ('pending', 'retry')) OR status = 'processing')
                     AND next_attempt_at <= ?
                   ORDER BY created_at LIMIT ?""",
                (now, limit),
            ).fetchall()
            for row in rows:
                updated = connection.execute(
                    """UPDATE mobile_push_outbox SET status = 'processing', next_attempt_at = ?
                       WHERE outbox_id = ? AND status = ? AND next_attempt_at <= ?""",
                    (lease_until, row["outbox_id"], row["status"], now),
                )
                if updated.rowcount == 1:
                    claimed.append({**row, "status": "processing",
                                    "payload": decode_json_value(row["payload_json"])})
        return tuple(claimed)

    def mark_delivered(self, outbox_id: str) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """UPDATE mobile_push_outbox SET status = 'delivered',
                   delivery_attempt = delivery_attempt + 1, delivered_at = ?,
                   last_error = NULL WHERE outbox_id = ? AND status != 'delivered'""",
                (datetime.now(UTC).isoformat(), outbox_id),
            )

    def mark_failed(self, outbox_id: str, error: str, *, max_attempts: int = 8) -> None:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT delivery_attempt FROM mobile_push_outbox WHERE outbox_id = ?",
                (outbox_id,),
            ).fetchone()
            if not row:
                return
            attempt = int(row["delivery_attempt"]) + 1
            status = "failed" if attempt >= max_attempts else "retry"
            next_attempt = (datetime.now(UTC) + timedelta(seconds=min(3600, 2 ** attempt))).isoformat()
            connection.execute(
                """UPDATE mobile_push_outbox SET status = ?, delivery_attempt = ?,
                   next_attempt_at = ?, last_error = ? WHERE outbox_id = ?""",
                (status, attempt, next_attempt, error[:500], outbox_id),
            )

    def get(self, outbox_id: str) -> dict[str, Any] | None:
        with self.storage.connect() as connection:
            return connection.execute(
                "SELECT * FROM mobile_push_outbox WHERE outbox_id = ?", (outbox_id,)
            ).fetchone()

    def register_device(self, actor_id: str, platform: str, token: str, role: str) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """INSERT INTO mobile_push_devices(actor_id, platform, token, role, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(actor_id, platform) DO UPDATE SET
                     token = excluded.token, role = excluded.role, updated_at = excluded.updated_at""",
                (actor_id, platform, token, role, datetime.now(UTC).isoformat()),
            )

    def devices_for(self, actor_id: str) -> tuple[dict[str, Any], ...]:
        with self.storage.connect() as connection:
            return connection.execute(
                "SELECT actor_id, platform, token, role FROM mobile_push_devices WHERE actor_id = ?",
                (actor_id,),
            ).fetchall()
