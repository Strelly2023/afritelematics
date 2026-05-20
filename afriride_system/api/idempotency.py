"""Adapter-layer idempotency for retry-safe HTTP commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable


@dataclass(frozen=True)
class IdempotencyRecord:
    fingerprint: str
    result: dict[str, Any]


class IdempotencyConflict(RuntimeError):
    """Raised when an idempotency key is reused for a different command."""


_store: dict[str, IdempotencyRecord] = {}


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

    if key in _store:
        record = _store[key]
        if fingerprint is not None and record.fingerprint != fingerprint:
            raise IdempotencyConflict("idempotency_key_reused_with_different_payload")
        return record.result

    result = operation()
    _store[key] = IdempotencyRecord(fingerprint=fingerprint or "", result=result)
    return result


def reset_idempotency_store() -> None:
    _store.clear()
