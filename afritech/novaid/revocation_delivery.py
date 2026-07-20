"""Versioned outbox publication and defensive Redis revocation consumption."""

from __future__ import annotations

import json
from threading import Event, Thread
from typing import Any

from .observability import NovaIDMetrics, NovaIDTracer
from .outbox import RevocationOutbox
from .persistence.postgres import PostgresNovaIdUnitOfWork


class RevocationPublisher:
    def __init__(
        self,
        outbox: RevocationOutbox,
        redis_client: Any,
        *,
        instance_id: str,
        metrics: NovaIDMetrics | None = None,
        tracer: NovaIDTracer | None = None,
    ) -> None:
        self.outbox, self.redis, self.instance_id = outbox, redis_client, instance_id
        self.metrics, self.tracer = metrics or NovaIDMetrics(), tracer or NovaIDTracer()
        self._stop, self._thread = Event(), None
        self.retries = 0

    def _outbox(self) -> RevocationOutbox:
        if hasattr(self.outbox.uow, "pool"):
            return RevocationOutbox(PostgresNovaIdUnitOfWork(pool=self.outbox.uow.pool))
        return self.outbox

    def publish_once(self, limit: int = 100) -> int:
        published = 0
        outbox = self._outbox()
        for row in outbox.claim(self.instance_id, limit=limit):
            with self.tracer.span("novaid.revocation.publish", {"operation": "revocation.publish"}):
                message = {
                    "event_id": str(row["outbox_id"]),
                    "event_type": row["event_type"],
                    "tenant_id": str(row["tenant_id"]),
                    "resource_type": row["resource_type"],
                    "resource_id": str(row["resource_id"]),
                    "event_version": int(row["event_version"]),
                    "occurred_at": str(row["created_at"]),
                    "schema_version": 1,
                }
                try:
                    self.redis.publish("novaid:revocations:v1", json.dumps(message))
                    with outbox.uow:
                        outbox.mark_published(str(row["outbox_id"]))
                    self.metrics.increment("novaid_revocation_publish_total", outcome="success")
                    published += 1
                except Exception as exc:
                    with outbox.uow:
                        outbox.mark_failed(str(row["outbox_id"]), type(exc).__name__)
                    self.metrics.increment("novaid_revocation_failures_total", outcome="failed")
                    self.retries += 1
        return published

    def start(self, *, poll_interval: float = 0.25, batch_size: int = 100) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()

        def run() -> None:
            while not self._stop.is_set():
                self.publish_once(batch_size)
                self._stop.wait(poll_interval)

        self._thread = Thread(target=run, name="novaid-outbox-publisher", daemon=True)
        self._thread.start()

    @property
    def healthy(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)


class RevocationConsumer:
    REQUIRED = {
        "event_id",
        "event_type",
        "tenant_id",
        "resource_type",
        "resource_id",
        "event_version",
        "occurred_at",
        "schema_version",
    }

    def __init__(
        self,
        redis_client: Any,
        *,
        uow: Any | None = None,
        metrics: NovaIDMetrics | None = None,
        tracer: NovaIDTracer | None = None,
    ) -> None:
        self.redis = redis_client
        self.uow = uow
        self.metrics, self.tracer = metrics or NovaIDMetrics(), tracer or NovaIDTracer()
        self._versions: dict[tuple[str, str, str], int] = {}
        self._seen: set[str] = set()
        self._stop, self._thread = Event(), None
        self.reconnects = 0

    def consume_message(self, raw: str) -> bool:
        with self.tracer.span("novaid.revocation.consume", {"operation": "revocation.consume"}):
            try:
                event = json.loads(raw)
                if not self.REQUIRED.issubset(event) or int(event["schema_version"]) != 1:
                    return False
                if not all(
                    str(event[key]) for key in ("tenant_id", "resource_type", "resource_id")
                ):
                    return False
                event_id = str(event["event_id"])
                if event_id in self._seen:
                    return True
                key = (
                    str(event["tenant_id"]),
                    str(event["resource_type"]),
                    str(event["resource_id"]),
                )
                version = int(event["event_version"])
                if version < self._versions.get(key, 0):
                    return True
                redis_key = f"novaid:revoked:{key[0]}:{key[1].lower()}:{key[2]}"
                self.redis.set(redis_key, str(version))
                self._versions[key], self._seen = version, self._seen | {event_id}
                self.metrics.increment("novaid_revocation_receive_total", outcome="success")
                return True
            except Exception:
                self.metrics.increment("novaid_redis_failures_total", outcome="malformed")
                return False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, name="novaid-revocation-consumer", daemon=True)
        self._thread.start()

    def rebuild_from_database(self) -> int:
        if self.uow is None:
            raise RuntimeError("revocation_database_unavailable")
        applied = 0
        sessions = self.uow.connection.execute(
            "SELECT tenant_id,session_id FROM novaid_authentication_sessions "
            "WHERE status IN ('REVOKED','EXPIRED','COMPROMISED','LOCKED')"
        ).fetchall()
        families = self.uow.connection.execute(
            "SELECT tenant_id,family_id FROM novaid_refresh_token_families WHERE status='REVOKED'"
        ).fetchall()
        for row in sessions:
            self.redis.set(f"novaid:revoked:{row['tenant_id']}:session:{row['session_id']}", "1")
            applied += 1
        for row in families:
            self.redis.set(f"novaid:revoked:{row['tenant_id']}:family:{row['family_id']}", "1")
            applied += 1
        return applied

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
                pubsub.subscribe("novaid:revocations:v1")
                for message in pubsub.listen():
                    if self._stop.is_set():
                        break
                    self.consume_message(message["data"])
            except Exception:
                self.reconnects += 1
                self.metrics.increment(
                    "novaid_revocation_consumer_reconnects_total", outcome="retry"
                )
                self._stop.wait(0.25)

    @property
    def healthy(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
