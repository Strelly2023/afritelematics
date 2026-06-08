"""Adapter-layer idempotency for retry-safe HTTP commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
from typing import Any, Callable

from afriride_system.backend.repositories.idempotency_repository import IdempotencyRepository


@dataclass(frozen=True)
class IdempotencyRecord:
    fingerprint: str
    result: dict[str, Any]


class IdempotencyConflict(RuntimeError):
    """Raised when an idempotency key is reused for a different command."""


_store: dict[str, IdempotencyRecord] = {}
_repository: IdempotencyRepository | None = None
_key_locks: dict[str, Lock] = {}
_key_locks_guard = Lock()


def command_fingerprint(command_name: str, payload: dict[str, Any]) -> str:
    """Return a deterministic fingerprint for a normalized API command."""

    canonical = json.dumps(
        {"command": command_name, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def run_once(
    key: str | None,
    operation: Callable[[], dict[str, Any]],
    *,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    if not key:
        return operation()

    with _lock_for(key):
        record = _record_for(key)
        if record is not None:
            if fingerprint is not None and record.fingerprint != fingerprint:
                raise IdempotencyConflict("idempotency_key_reused_with_different_payload")
            return record.result

        result = operation()
        stored = IdempotencyRecord(fingerprint=fingerprint or "", result=result)
        if _repository is not None:
            _repository.save(key, stored.fingerprint, stored.result)
        else:
            _store[key] = stored
        return result


def configure_idempotency_repository(repository: IdempotencyRepository | None) -> None:
    global _repository
    _repository = repository
    if repository is not None:
        _store.clear()


def reset_idempotency_store() -> None:
    with _key_locks_guard:
        _key_locks.clear()
    if _repository is not None:
        _repository.clear()
        return
    _store.clear()


def _record_for(key: str) -> IdempotencyRecord | None:
    if _repository is not None:
        persisted = _repository.get(key)
        if persisted is None:
            return None
        return IdempotencyRecord(
            fingerprint=persisted.fingerprint,
            result=persisted.result,
        )
    return _store.get(key)


def _lock_for(key: str) -> Lock:
    with _key_locks_guard:
        lock = _key_locks.get(key)
        if lock is None:
            lock = Lock()
            _key_locks[key] = lock
        return lock
