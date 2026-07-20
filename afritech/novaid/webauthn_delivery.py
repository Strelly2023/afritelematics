"""Durable Redis Streams delivery for NovaID WebAuthn state."""
# ruff: noqa: E501 -- explicit delivery SQL is part of the security contract.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from threading import Event, Thread
from typing import Any
from uuid import uuid4

from .observability import NovaIDMetrics, NovaIDTracer


FORBIDDEN = {
    "challenge",
    "recovery_code",
    "access_token",
    "refresh_token",
    "public_key",
    "attestation_certificate",
    "signature",
    "private_key",
    "secret",
}
EVENT_TYPES = {
    "WEBAUTHN_CHALLENGE_CREATED",
    "WEBAUTHN_CHALLENGE_SUPERSEDED",
    "WEBAUTHN_CHALLENGE_CONSUMED",
    "WEBAUTHN_CHALLENGE_EXPIRED",
    "WEBAUTHN_CREDENTIAL_REGISTERED",
    "WEBAUTHN_CREDENTIAL_SUSPENDED",
    "WEBAUTHN_CREDENTIAL_REACTIVATED",
    "WEBAUTHN_CREDENTIAL_REVOKED",
    "WEBAUTHN_CREDENTIAL_COMPROMISED",
    "WEBAUTHN_CREDENTIAL_REPLACED",
    "TENANT_WEBAUTHN_POLICY_CREATED",
    "TENANT_WEBAUTHN_POLICY_UPDATED",
    "TENANT_WEBAUTHN_POLICY_ACTIVATED",
    "TENANT_WEBAUTHN_POLICY_SUPERSEDED",
    "TENANT_WEBAUTHN_POLICY_ROLLED_BACK",
    "IDENTITY_SECURITY_VERSION_INCREMENTED",
    "ACCOUNT_RECOVERY_COMPLETED",
    "ACCOUNT_RECOVERY_REJECTED",
    "ACCOUNT_RECOVERY_CANCELLED",
    "ACCOUNT_RECOVERY_EXPIRED",
    "RECOVERY_REENROLMENT_REQUIRED",
    "ALL_SESSIONS_REVOKED",
    "SESSION_REVOKED",
    "TOKEN_FAMILY_REVOKED",
    "WEBAUTHN_DISTRIBUTED_VERSION_CONFLICT",
    "WEBAUTHN_DEAD_LETTER_REPLAY_REQUESTED",
    "WEBAUTHN_DEAD_LETTER_REPLAY_APPROVED",
    "WEBAUTHN_DEAD_LETTER_REPLAY_REJECTED",
    "WEBAUTHN_DEAD_LETTER_REPLAYED",
    "WEBAUTHN_OUTBOX_EVENT_CREATED",
    "WEBAUTHN_OUTBOX_EVENT_CLAIMED",
    "WEBAUTHN_OUTBOX_EVENT_PUBLISHED",
    "WEBAUTHN_OUTBOX_EVENT_RETRY_SCHEDULED",
    "WEBAUTHN_OUTBOX_EVENT_DEAD_LETTERED",
    "WEBAUTHN_OUTBOX_EVENT_REPLAY_REQUESTED",
    "WEBAUTHN_OUTBOX_EVENT_REPLAYED",
    "WEBAUTHN_EVENT_RECEIVED",
    "WEBAUTHN_EVENT_APPLIED",
    "WEBAUTHN_EVENT_DUPLICATE_IGNORED",
    "WEBAUTHN_EVENT_STALE_IGNORED",
    "WEBAUTHN_EVENT_VERSION_CONFLICT",
    "WEBAUTHN_EVENT_MALFORMED_REJECTED",
    "WEBAUTHN_CONSUMER_RECONNECTED",
}


class CheckpointOutcome:
    NEWER_EVENT = "NEWER_EVENT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    STALE_EVENT = "STALE_EVENT"
    VERSION_CONFLICT = "VERSION_CONFLICT"


class WebAuthnCheckpointRepository:
    def __init__(self, uow) -> None:
        self.uow = uow
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.uow.connection.execute(
            "CREATE TABLE IF NOT EXISTS novaid_webauthn_event_checkpoints("
            "consumer_name text NOT NULL,tenant_id text NOT NULL,resource_type text NOT NULL DEFAULT '',"
            "resource_reference text NOT NULL DEFAULT '',event_version integer NOT NULL CHECK(event_version>=0),"
            "updated_at timestamptz NOT NULL,last_event_id text,last_stream_id text,applied_at timestamptz,"
            "PRIMARY KEY(consumer_name,tenant_id,resource_type,resource_reference))"
        )
        if hasattr(self.uow, "pool"):
            try:
                columns = {
                    row["column_name"]
                    for row in self.uow.connection.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='novaid_webauthn_event_checkpoints'"
                    ).fetchall()
                }
                if "last_stream_id" not in columns:
                    self.uow.connection.execute(
                        "ALTER TABLE novaid_webauthn_event_checkpoints ADD COLUMN last_stream_id text"
                    )
            except Exception as exc:  # pragma: no cover - runtime bootstrap guard
                if "duplicate column" not in str(exc).lower():
                    raise
        else:
            columns = {
                row[1]
                for row in self.uow.connection.execute(
                    "PRAGMA table_info(novaid_webauthn_event_checkpoints)"
                ).fetchall()
            }
            if "last_stream_id" not in columns:
                self.uow.connection.execute(
                    "ALTER TABLE novaid_webauthn_event_checkpoints ADD COLUMN last_stream_id TEXT"
                )

    def _suffix(self) -> str:
        return " FOR UPDATE" if hasattr(self.uow, "pool") else ""

    def get_checkpoint(
        self, *, consumer_name: str, tenant_id: str, resource_type: str, resource_reference: str
    ):
        return self.uow.connection.execute(
            "SELECT * FROM novaid_webauthn_event_checkpoints WHERE consumer_name=? AND tenant_id=? "
            "AND resource_type=? AND resource_reference=?",
            (consumer_name, tenant_id, resource_type, resource_reference),
        ).fetchone()

    def lock_checkpoint(
        self, *, consumer_name: str, tenant_id: str, resource_type: str, resource_reference: str
    ):
        return self.uow.connection.execute(
            "SELECT * FROM novaid_webauthn_event_checkpoints WHERE consumer_name=? AND tenant_id=? "
            "AND resource_type=? AND resource_reference=?" + self._suffix(),
            (consumer_name, tenant_id, resource_type, resource_reference),
        ).fetchone()

    def create_checkpoint(
        self,
        *,
        consumer_name: str,
        tenant_id: str,
        resource_type: str,
        resource_reference: str,
        event_version: int = 0,
        last_event_id: str | None = None,
        last_stream_id: str | None = None,
    ):
        now = datetime.now(UTC).isoformat()
        self.uow.connection.execute(
            "INSERT INTO novaid_webauthn_event_checkpoints("
            "consumer_name,tenant_id,resource_type,resource_reference,event_version,updated_at,"
            "last_event_id,last_stream_id,applied_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                consumer_name,
                tenant_id,
                resource_type,
                resource_reference,
                event_version,
                now,
                last_event_id,
                last_stream_id,
                now if event_version else None,
            ),
        )
        return self.get_checkpoint(
            consumer_name=consumer_name,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_reference=resource_reference,
        )

    def classify(
        self,
        *,
        consumer_name: str,
        tenant_id: str,
        resource_type: str,
        resource_reference: str,
        event_version: int,
        event_id: str,
    ) -> str:
        checkpoint = self.get_checkpoint(
            consumer_name=consumer_name,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_reference=resource_reference,
        )
        if not checkpoint:
            return CheckpointOutcome.NEWER_EVENT
        current = int(checkpoint["event_version"])
        if event_id and checkpoint["last_event_id"] == event_id:
            return CheckpointOutcome.DUPLICATE_EVENT
        if event_version < current:
            return CheckpointOutcome.STALE_EVENT
        if event_version == current:
            return CheckpointOutcome.VERSION_CONFLICT
        return CheckpointOutcome.NEWER_EVENT

    def detect_duplicate(self, **kwargs) -> bool:
        return self.classify(**kwargs) == CheckpointOutcome.DUPLICATE_EVENT

    def detect_stale(self, **kwargs) -> bool:
        return self.classify(**kwargs) == CheckpointOutcome.STALE_EVENT

    def detect_same_version_conflict(self, **kwargs) -> bool:
        return self.classify(**kwargs) == CheckpointOutcome.VERSION_CONFLICT

    def advance_checkpoint(
        self,
        *,
        consumer_name: str,
        tenant_id: str,
        resource_type: str,
        resource_reference: str,
        event_version: int,
        event_id: str,
        stream_id: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        checkpoint = self.lock_checkpoint(
            consumer_name=consumer_name,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_reference=resource_reference,
        )
        if not checkpoint:
            self.create_checkpoint(
                consumer_name=consumer_name,
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_reference=resource_reference,
                event_version=event_version,
                last_event_id=event_id,
                last_stream_id=stream_id,
            )
            return
        current = int(checkpoint["event_version"])
        if event_version <= current:
            return
        self.uow.connection.execute(
            "UPDATE novaid_webauthn_event_checkpoints SET event_version=?,updated_at=?,"
            "last_event_id=?,last_stream_id=?,applied_at=? WHERE consumer_name=? AND tenant_id=? "
            "AND resource_type=? AND resource_reference=?",
            (
                event_version,
                now,
                event_id,
                stream_id,
                now,
                consumer_name,
                tenant_id,
                resource_type,
                resource_reference,
            ),
        )


class WebAuthnOutboxRepository:
    def __init__(self, uow) -> None:
        self.uow = uow

    def create_event(
        self,
        *,
        tenant_id: str,
        event_type: str,
        resource_type: str,
        resource_reference: str,
        resource_version: int,
        correlation_id: str,
        request_id: str,
        payload: dict[str, object],
    ) -> str:
        if event_type not in EVENT_TYPES or resource_version < 1:
            raise ValueError("invalid_webauthn_event")
        if FORBIDDEN & {key.lower() for key in payload}:
            raise ValueError("secret_in_webauthn_event")
        event_id, now = str(uuid4()), datetime.now(UTC).isoformat()
        self.uow.connection.execute(
            "INSERT INTO novaid_webauthn_outbox(outbox_id,tenant_id,event_type,resource_id,"
            "event_version,payload,status,created_at,available_at,attempt_count,version,"
            "correlation_id,request_id,resource_type) "
            "VALUES(?,?,?,?,?,?,'PENDING',?,?,0,1,?,?,?)",
            (
                event_id,
                tenant_id,
                event_type,
                resource_reference,
                resource_version,
                json.dumps(payload),
                now,
                now,
                correlation_id,
                request_id,
                resource_type,
            ),
        )
        return event_id

    def claim_pending_batch(self, owner: str, *, limit: int = 100, lease_seconds: int = 30):
        now, lease, claimed = (
            datetime.now(UTC),
            datetime.now(UTC) + timedelta(seconds=lease_seconds),
            [],
        )
        with self.uow:
            suffix = " FOR UPDATE SKIP LOCKED" if hasattr(self.uow, "pool") else ""
            rows = self.uow.connection.execute(
                "SELECT * FROM novaid_webauthn_outbox WHERE status IN ('PENDING','FAILED') "
                "AND COALESCE(next_attempt_at,available_at)<=? AND "
                "(lease_expires_at IS NULL OR lease_expires_at<=?) ORDER BY created_at LIMIT ?"
                + suffix,
                (now.isoformat(), now.isoformat(), limit),
            ).fetchall()
            for row in rows:
                changed = self.uow.connection.execute(
                    "UPDATE novaid_webauthn_outbox SET status='PUBLISHING',lease_owner=?,"
                    "lease_expires_at=?,last_attempt_at=?,attempt_count=attempt_count+1 "
                    "WHERE outbox_id=? AND status IN ('PENDING','FAILED')",
                    (owner, lease.isoformat(), now.isoformat(), row["outbox_id"]),
                )
                if changed.rowcount == 1:
                    claimed.append(row)
        return claimed

    def mark_published(self, event_id: str, owner: str) -> None:
        self.uow.connection.execute(
            "UPDATE novaid_webauthn_outbox SET status='PUBLISHED',published_at=?,lease_owner=NULL,"
            "lease_expires_at=NULL,last_error=NULL WHERE outbox_id=? AND lease_owner=?",
            (datetime.now(UTC).isoformat(), event_id, owner),
        )

    def mark_failed(self, event_id: str, owner: str, error: str, *, maximum_attempts: int) -> None:
        row = self.uow.connection.execute(
            "SELECT attempt_count FROM novaid_webauthn_outbox WHERE outbox_id=? AND lease_owner=?",
            (event_id, owner),
        ).fetchone()
        if not row:
            return
        dead = int(row["attempt_count"]) >= maximum_attempts
        delay = min(300, 2 ** min(int(row["attempt_count"]), 8))
        self.uow.connection.execute(
            "UPDATE novaid_webauthn_outbox SET status=?,last_error=?,dead_letter_reason=?,"
            "next_attempt_at=?,lease_owner=NULL,lease_expires_at=NULL WHERE outbox_id=?",
            (
                "DEAD_LETTER" if dead else "FAILED",
                error[:128],
                error[:128] if dead else None,
                (datetime.now(UTC) + timedelta(seconds=delay)).isoformat(),
                event_id,
            ),
        )

    def list_dead_letters(self, *, tenant_id: str, limit: int = 100) -> list[dict[str, object]]:
        return self.uow.connection.execute(
            "SELECT outbox_id,tenant_id,event_type,resource_type,resource_id,event_version,"
            "status,created_at,available_at,published_at,attempt_count,version,correlation_id,"
            "request_id,last_error,dead_letter_reason "
            "FROM novaid_webauthn_outbox WHERE tenant_id=? AND status='DEAD_LETTER' "
            "ORDER BY created_at DESC LIMIT ?",
            (tenant_id, limit),
        ).fetchall()

    def latest_resource_version(
        self, *, tenant_id: str, resource_type: str, resource_reference: str
    ) -> int:
        row = self.uow.connection.execute(
            "SELECT MAX(event_version) AS version FROM novaid_webauthn_outbox "
            "WHERE tenant_id=? AND resource_type=? AND resource_id=? "
            "AND status IN ('PENDING','PUBLISHING','PUBLISHED','FAILED','DEAD_LETTER')",
            (tenant_id, resource_type, resource_reference),
        ).fetchone()
        return int(row["version"] or 0) if row else 0

    def replay_dead_letter(
        self,
        *,
        event_id: str,
        tenant_id: str,
        reason: str,
        actor_identity_id: str,
    ) -> dict[str, object]:
        row = self.uow.connection.execute(
            "SELECT * FROM novaid_webauthn_outbox WHERE outbox_id=? AND tenant_id=?",
            (event_id, tenant_id),
        ).fetchone()
        if not row or row["status"] != "DEAD_LETTER":
            raise ValueError("dead_letter_not_found")
        current = self.latest_resource_version(
            tenant_id=tenant_id,
            resource_type=str(row["resource_type"]),
            resource_reference=str(row["resource_id"]),
        )
        if int(row["event_version"]) < current:
            raise ValueError("dead_letter_stale")
        self.uow.connection.execute(
            "UPDATE novaid_webauthn_outbox SET status='PENDING',available_at=?,next_attempt_at=NULL,"
            "lease_owner=NULL,lease_expires_at=NULL,last_error=NULL,dead_letter_reason=NULL,"
            "version=version+1 WHERE outbox_id=? AND tenant_id=?",
            (datetime.now(UTC).isoformat(), event_id, tenant_id),
        )
        return {
            "event_id": event_id,
            "tenant_id": tenant_id,
            "reason": reason,
            "actor_identity_id": actor_identity_id,
            "resource_type": str(row["resource_type"]),
            "resource_reference": str(row["resource_id"]),
            "event_version": int(row["event_version"]),
        }


class WebAuthnOutboxPublisher:
    STREAM = "novaid:webauthn:events:v1"

    def __init__(
        self,
        repository: WebAuthnOutboxRepository,
        redis_client: Any,
        *,
        instance_id: str,
        maximum_attempts: int = 5,
        metrics=None,
        tracer=None,
    ) -> None:
        self.repository, self.redis, self.instance_id = repository, redis_client, instance_id
        self.maximum_attempts = maximum_attempts
        self.metrics, self.tracer = metrics or NovaIDMetrics(), tracer or NovaIDTracer()
        self._stop, self._thread = Event(), None
        self.retries = self.dead_letters = self.published = 0

    def _repository(self) -> WebAuthnOutboxRepository:
        if hasattr(self.repository.uow, "pool"):
            from .persistence.postgres import PostgresNovaIdUnitOfWork

            return WebAuthnOutboxRepository(PostgresNovaIdUnitOfWork(pool=self.repository.uow.pool))
        return self.repository

    def publish_once(self, limit: int = 100) -> int:
        count = 0
        repository = self._repository()
        for row in repository.claim_pending_batch(self.instance_id, limit=limit):
            envelope = {
                "event_id": str(row["outbox_id"]),
                "schema_version": 1,
                "event_type": row["event_type"],
                "tenant_id": str(row["tenant_id"]),
                "resource_type": row["resource_type"],
                "resource_reference": str(row["resource_id"]),
                "resource_version": int(row["event_version"]),
                "occurred_at": str(row["created_at"]),
                "published_at": datetime.now(UTC).isoformat(),
                "producer_instance_id": self.instance_id,
                "correlation_id": row["correlation_id"],
                "request_id": row["request_id"],
                "payload": row["payload"],
            }
            try:
                self.redis.xadd(self.STREAM, {"event": json.dumps(envelope)}, maxlen=10000)
                with repository.uow:
                    repository.mark_published(str(row["outbox_id"]), self.instance_id)
                self.published += 1
                count += 1
            except Exception as exc:
                with repository.uow:
                    repository.mark_failed(
                        str(row["outbox_id"]),
                        self.instance_id,
                        type(exc).__name__,
                        maximum_attempts=self.maximum_attempts,
                    )
                self.retries += 1
        return count

    def start(self, interval: float = 0.25) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(
            target=lambda: self._run(interval), daemon=True, name="novaid-webauthn-publisher"
        )
        self._thread.start()

    def _run(self, interval: float) -> None:
        while not self._stop.is_set():
            self.publish_once()
            self._stop.wait(interval)

    @property
    def healthy(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)


class WebAuthnDistributedEventConsumer:
    STREAM = WebAuthnOutboxPublisher.STREAM

    def __init__(self, redis_client: Any, *, consumer_name: str, metrics=None, uow=None) -> None:
        self.redis, self.consumer_name = redis_client, consumer_name
        self.metrics = metrics or NovaIDMetrics()
        self.uow = uow
        self.checkpoints = WebAuthnCheckpointRepository(uow) if uow is not None else None
        self.duplicates = self.stale = self.reconnects = self.applied = 0
        self._stop, self._thread = Event(), None

    def apply(self, envelope: dict[str, object]) -> bool:
        if envelope.get("schema_version") != 1 or envelope.get("event_type") not in EVENT_TYPES:
            self.metrics.increment("novaid_webauthn_events_malformed_total", outcome="rejected")
            return False
        tenant, resource_type = str(envelope["tenant_id"]), str(envelope["resource_type"])
        resource, event_id = str(envelope["resource_reference"]), str(envelope["event_id"])
        version = int(envelope["resource_version"])
        seen_key = f"novaid:v1:event:{event_id}"
        version_key = f"novaid:v1:version:{tenant}:{resource_type}:{resource}"
        if self.checkpoints is not None:
            outcome = self.checkpoints.classify(
                consumer_name=self.consumer_name,
                tenant_id=tenant,
                resource_type=resource_type,
                resource_reference=resource,
                event_version=version,
                event_id=event_id,
            )
            if outcome == CheckpointOutcome.DUPLICATE_EVENT:
                self.duplicates += 1
                self.metrics.increment("novaid_webauthn_events_duplicate_total", outcome="ignored")
                return True
            if outcome == CheckpointOutcome.STALE_EVENT:
                self.stale += 1
                self.metrics.increment("novaid_webauthn_events_stale_total", outcome="ignored")
                return True
            if outcome == CheckpointOutcome.VERSION_CONFLICT:
                self.stale += 1
                self.metrics.increment("novaid_webauthn_events_conflict_total", outcome="rejected")
                self.redis.hset(
                    f"novaid:v1:state:{tenant}:{resource_type}:{resource}",
                    mapping={"event_type": "WEBAUTHN_DISTRIBUTED_VERSION_CONFLICT", "version": version},
                )
                return False
        else:
            if self.redis.exists(seen_key):
                self.duplicates += 1
                self.metrics.increment("novaid_webauthn_events_duplicate_total", outcome="ignored")
                return True
            current = int(self.redis.get(version_key) or 0)
            if version < current:
                self.stale += 1
                self.metrics.increment("novaid_webauthn_events_stale_total", outcome="ignored")
                return True
            if version == current and current:
                self.stale += 1
                self.metrics.increment("novaid_webauthn_events_conflict_total", outcome="rejected")
                return False
        event_type = str(envelope["event_type"])
        state_key = f"novaid:v1:state:{tenant}:{resource_type}:{resource}"
        if self.checkpoints is not None:
            with self.uow:
                self.checkpoints.advance_checkpoint(
                    consumer_name=self.consumer_name,
                    tenant_id=tenant,
                    resource_type=resource_type,
                    resource_reference=resource,
                    event_version=version,
                    event_id=event_id,
                    stream_id=str(envelope.get("stream_id") or ""),
                )
        self.redis.hset(state_key, mapping={"event_type": event_type, "version": version})
        if event_type.startswith("TENANT_WEBAUTHN_POLICY_"):
            self.redis.delete(f"novaid:v1:tenant:{tenant}:webauthn:policy")
        self.redis.set(version_key, version)
        self.redis.set(seen_key, "1", ex=86400)
        self.applied += 1
        self.metrics.increment("novaid_webauthn_events_applied_total", outcome="success")
        return True

    def consume_available(self) -> int:
        entries = self.redis.xrange(self.STREAM, min="-", max="+")
        count = 0
        for stream_id, fields in entries:
            raw = fields.get("event") or fields.get(b"event")
            if isinstance(raw, bytes):
                raw = raw.decode()
            try:
                envelope = json.loads(raw)
                if isinstance(envelope, dict):
                    envelope["stream_id"] = str(stream_id)
                if self.apply(envelope):
                    count += 1
            except Exception:
                continue
        return count

    def start(self, interval: float = 0.5) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(
            target=lambda: self._run(interval), daemon=True, name="novaid-webauthn-consumer"
        )
        self._thread.start()

    def _run(self, interval: float) -> None:
        while not self._stop.is_set():
            try:
                self.consume_available()
            except Exception:
                self.reconnects += 1
            self._stop.wait(interval)

    @property
    def healthy(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)


class TenantWebAuthnPolicyCache:
    def __init__(
        self, redis_client: Any, authoritative_service: Any, *, ttl_seconds: int = 300
    ) -> None:
        self.redis, self.service, self.ttl = redis_client, authoritative_service, ttl_seconds

    def get(self, tenant_id: str) -> dict[str, object]:
        key = f"novaid:v1:tenant:{tenant_id}:webauthn:policy"
        cached = self.redis.get(key)
        if cached:
            value = json.loads(cached)
            if isinstance(value.get("version"), int) and value["version"] >= 0:
                return value["policy"]
            self.redis.delete(key)
        policy = self.service.get_policy(tenant_id)
        serialized = json.dumps(policy, sort_keys=True, separators=(",", ":"))
        wrapper = {
            "version": int(policy["version"]),
            "digest": hashlib.sha256(serialized.encode()).hexdigest(),
            "active": True,
            "policy": policy,
            "cached_at": datetime.now(UTC).isoformat(),
        }
        self.redis.set(key, json.dumps(wrapper), ex=self.ttl)
        return policy
