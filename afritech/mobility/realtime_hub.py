"""Versioned real-time mobility event log and presence registry."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import os
import socket
from threading import RLock
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True)
class MobilityEvent:
    stream_id: str
    sequence: int | None
    event_type: str
    partition: str
    producer_id: str
    trace_id: str
    targets: frozenset[str]
    data: dict[str, Any]
    published_at: str
    delivery_attempt: int = 0

    def payload(self) -> dict[str, Any]:
        return {
            "contract": "afriride.mobility.v1",
            "type": self.event_type,
            "stream_id": self.stream_id,
            "sequence": self.sequence,
            "partition": self.partition,
            "producer_id": self.producer_id,
            "trace_id": self.trace_id,
            "published_at": self.published_at,
            "occurred_at": self.published_at,
            "delivery_attempt": self.delivery_attempt,
            "authority": "server_projection",
            "data": deepcopy(self.data),
        }


class MobilityHub:
    """Process-local event log with replay cursors and expiring presence."""

    def __init__(self, *, max_events: int = 10_000, presence_ttl_seconds: int = 45) -> None:
        self._events: deque[MobilityEvent] = deque(maxlen=max_events)
        self._presence: dict[str, datetime] = {}
        self._sequence = 0
        self._presence_ttl = timedelta(seconds=presence_ttl_seconds)
        self._lock = RLock()
        self.producer_id = os.environ.get("AFRIRIDE_PRODUCER_ID", socket.gethostname())

    def publish(
        self,
        event_type: str,
        *,
        targets: set[str],
        data: dict[str, Any],
        partition: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        if not targets:
            raise ValueError("mobility event requires at least one target")
        with self._lock:
            self._sequence += 1
            event = MobilityEvent(
                stream_id=f"{int(datetime.now(UTC).timestamp() * 1000)}-{self._sequence}",
                sequence=self._sequence,
                event_type=event_type,
                partition=partition or sorted(targets)[0],
                producer_id=self.producer_id,
                trace_id=trace_id or uuid4().hex,
                targets=frozenset(targets),
                data=deepcopy(data),
                published_at=datetime.now(UTC).isoformat(),
            )
            self._events.append(event)
            return event.payload()

    def events_after(self, cursor: str | int, targets: set[str]) -> list[dict[str, Any]]:
        numeric_cursor = _numeric_cursor(cursor)
        with self._lock:
            return [
                event.payload()
                for event in self._events
                if (event.sequence or 0) > numeric_cursor and event.targets.intersection(targets)
            ]

    def heartbeat(self, actor_id: str) -> dict[str, Any]:
        now = datetime.now(UTC)
        with self._lock:
            self._presence[actor_id] = now
        return {
            "actor_id": actor_id,
            "status": "online",
            "last_seen_at": now.isoformat(),
            "expires_in_seconds": int(self._presence_ttl.total_seconds()),
        }

    def presence(self, actor_id: str) -> dict[str, Any]:
        with self._lock:
            last_seen = self._presence.get(actor_id)
        online = bool(last_seen and datetime.now(UTC) - last_seen <= self._presence_ttl)
        return {
            "actor_id": actor_id,
            "status": "online" if online else "offline",
            "last_seen_at": last_seen.isoformat() if last_seen else None,
        }

    def disconnect(self, actor_id: str) -> None:
        # Retain last_seen so transient network changes do not flap presence.
        with self._lock:
            self._presence.setdefault(actor_id, datetime.now(UTC) - self._presence_ttl)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._presence.clear()
            self._sequence = 0


class MobilityHubRepository(Protocol):
    def publish(self, event_type: str, *, targets: set[str], data: dict[str, Any],
                partition: str | None = None, trace_id: str | None = None) -> dict[str, Any]: ...
    def events_after(self, cursor: str | int, targets: set[str]) -> list[dict[str, Any]]: ...
    def heartbeat(self, actor_id: str) -> dict[str, Any]: ...
    def presence(self, actor_id: str) -> dict[str, Any]: ...
    def disconnect(self, actor_id: str) -> None: ...


class RedisMobilityHub:
    """Shared Redis Streams event log and TTL presence adapter."""

    def __init__(self, redis_client, *, stream_prefix: str = "mobility",
                 presence_ttl_seconds: int = 45, max_events: int = 100_000) -> None:
        self.redis = redis_client
        self.stream_prefix = stream_prefix
        self.presence_ttl = presence_ttl_seconds
        self.max_events = max_events
        self.producer_id = os.environ.get("AFRIRIDE_PRODUCER_ID", socket.gethostname())

    @classmethod
    def from_url(cls, url: str) -> "RedisMobilityHub":
        import redis
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        return cls(client)

    def _stream(self, target: str) -> str:
        return f"{self.stream_prefix}:{target}"

    def publish(self, event_type: str, *, targets: set[str], data: dict[str, Any],
                partition: str | None = None, trace_id: str | None = None) -> dict[str, Any]:
        primary = partition or sorted(targets)[0]
        envelope = {
            "contract": "afriride.mobility.v1",
            "type": event_type,
            "partition": primary,
            "producer_id": self.producer_id,
            "trace_id": trace_id or uuid4().hex,
            "published_at": datetime.now(UTC).isoformat(),
            "delivery_attempt": 0,
            "authority": "server_projection",
            "data": deepcopy(data),
        }
        event_key = uuid4().hex
        fields = {"event_id": event_key, "envelope": json.dumps(envelope, separators=(",", ":"), default=str)}
        stream_id = None
        for target in sorted(targets):
            added = self.redis.xadd(self._stream(target), fields, maxlen=self.max_events, approximate=True)
            stream_id = stream_id or str(added)
        return {**envelope, "stream_id": stream_id, "sequence": None, "occurred_at": envelope["published_at"]}

    def events_after(self, cursor: str | int, targets: set[str]) -> list[dict[str, Any]]:
        redis_cursor = _redis_cursor(cursor)
        streams = {self._stream(target): redis_cursor for target in targets}
        rows = self.redis.xread(streams, count=500, block=1) if streams else []
        deduplicated: dict[str, dict[str, Any]] = {}
        for _, messages in rows:
            for stream_id, fields in messages:
                event = json.loads(fields["envelope"])
                event["stream_id"] = str(stream_id)
                event["sequence"] = None
                event["occurred_at"] = event["published_at"]
                deduplicated[fields["event_id"]] = event
        return sorted(deduplicated.values(), key=lambda item: _stream_tuple(item["stream_id"]))

    def heartbeat(self, actor_id: str) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        self.redis.set(f"presence:{actor_id}", now, ex=self.presence_ttl)
        return {"actor_id": actor_id, "status": "online", "last_seen_at": now,
                "expires_in_seconds": self.presence_ttl}

    def presence(self, actor_id: str) -> dict[str, Any]:
        last_seen = self.redis.get(f"presence:{actor_id}")
        return {"actor_id": actor_id, "status": "online" if last_seen else "offline",
                "last_seen_at": last_seen}

    def disconnect(self, actor_id: str) -> None:
        # TTL remains authoritative to absorb transient disconnects.
        _ = actor_id


def _numeric_cursor(cursor: str | int) -> int:
    text = str(cursor)
    if "-" in text:
        return int(text.rsplit("-", 1)[-1])
    return int(text or 0)


def _redis_cursor(cursor: str | int) -> str:
    text = str(cursor or "0")
    return text if "-" in text else f"0-{int(text)}"


def _stream_tuple(stream_id: str) -> tuple[int, int]:
    milliseconds, sequence = stream_id.split("-", 1)
    return int(milliseconds), int(sequence)


def build_mobility_hub() -> MobilityHubRepository:
    backend = os.environ.get("AFRIRIDE_REALTIME_BACKEND", "memory").lower()
    if backend == "memory":
        return MobilityHub()
    if backend != "redis":
        raise RuntimeError(f"unsupported realtime backend: {backend}")
    redis_url = os.environ.get("AFRIRIDE_REDIS_URL") or os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("AFRIRIDE_REDIS_URL is required for Redis realtime backend")
    return RedisMobilityHub.from_url(redis_url)


mobility_hub = build_mobility_hub()
