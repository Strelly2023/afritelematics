"""Durable, secret-rejecting revocation outbox."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from uuid import uuid4


FORBIDDEN = {"token", "password", "otp", "secret", "signature", "credential_hash"}


class RevocationOutbox:
    def __init__(self, uow) -> None:
        self.uow = uow

    def enqueue(
        self,
        *,
        tenant_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        event_version: int,
        payload: dict[str, object],
    ) -> str:
        if FORBIDDEN & {key.lower() for key in payload}:
            raise ValueError("secret_in_revocation_outbox")
        outbox_id, now = str(uuid4()), datetime.now(UTC)
        self.uow.connection.execute(
            "INSERT INTO novaid_security_outbox(outbox_id,tenant_id,event_type,resource_type,"
            "resource_id,event_version,payload,created_at,status) "
            "VALUES(?,?,?,?,?,?,?,?, 'PENDING')",
            (
                outbox_id,
                tenant_id,
                event_type,
                resource_type,
                resource_id,
                event_version,
                json.dumps(payload),
                now.isoformat(),
            ),
        )
        return outbox_id

    def pending(self, limit: int = 100) -> list[dict[str, object]]:
        return self.uow.connection.execute(
            "SELECT * FROM novaid_security_outbox WHERE status IN ('PENDING','FAILED') "
            "AND (next_attempt_at IS NULL OR next_attempt_at<=?) ORDER BY created_at LIMIT ?",
            (datetime.now(UTC).isoformat(), limit),
        ).fetchall()

    def mark_published(self, outbox_id: str) -> None:
        self.uow.connection.execute(
            "UPDATE novaid_security_outbox SET status='PUBLISHED',published_at=?,last_error=NULL,"
            "lease_owner=NULL,lease_expires_at=NULL "
            "WHERE outbox_id=?",
            (datetime.now(UTC).isoformat(), outbox_id),
        )

    def mark_failed(self, outbox_id: str, error_code: str) -> None:
        if len(error_code) > 128:
            error_code = error_code[:128]
        self.uow.connection.execute(
            "UPDATE novaid_security_outbox SET status=CASE "
            "WHEN attempt_count>=9 THEN 'DEAD_LETTER' "
            "ELSE 'FAILED' END,attempt_count=attempt_count+1,last_error=?,next_attempt_at=?,"
            "lease_owner=NULL,lease_expires_at=NULL "
            "WHERE outbox_id=?",
            (error_code, (datetime.now(UTC) + timedelta(seconds=30)).isoformat(), outbox_id),
        )

    def claim(
        self, owner: str, *, limit: int = 100, lease_seconds: int = 30
    ) -> list[dict[str, object]]:
        now, lease = datetime.now(UTC), datetime.now(UTC) + timedelta(seconds=lease_seconds)
        with self.uow:
            if hasattr(self.uow, "pool"):
                rows = self.uow.connection.execute(
                    "SELECT * FROM novaid_security_outbox WHERE status IN ('PENDING','FAILED') "
                    "AND COALESCE(next_attempt_at,available_at,created_at)<=? "
                    "AND (lease_expires_at IS NULL OR lease_expires_at<=?) "
                    "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT ?",
                    (now.isoformat(), now.isoformat(), limit),
                ).fetchall()
            else:
                rows = self.uow.connection.execute(
                    "SELECT * FROM novaid_security_outbox WHERE status IN ('PENDING','FAILED') "
                    "AND COALESCE(next_attempt_at,available_at,created_at)<=? "
                    "AND (lease_expires_at IS NULL OR lease_expires_at<=?) "
                    "ORDER BY created_at LIMIT ?",
                    (now.isoformat(), now.isoformat(), limit),
                ).fetchall()
            claimed = []
            for row in rows:
                changed = self.uow.connection.execute(
                    "UPDATE novaid_security_outbox SET status='PUBLISHING',lease_owner=?,"
                    "lease_expires_at=?,last_attempt_at=?,attempt_count=attempt_count+1 "
                    "WHERE outbox_id=? AND status IN ('PENDING','FAILED')",
                    (owner, lease.isoformat(), now.isoformat(), row["outbox_id"]),
                )
                if changed.rowcount == 1:
                    claimed.append(row)
        return claimed
