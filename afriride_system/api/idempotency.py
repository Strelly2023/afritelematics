"""Adapter-layer idempotency for retry-safe HTTP commands."""

from __future__ import annotations

from typing import Any, Callable

_store: dict[str, dict[str, Any]] = {}


def run_once(key: str | None, operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    if not key:
        return operation()

    if key in _store:
        return _store[key]

    result = operation()
    _store[key] = result
    return result


def reset_idempotency_store() -> None:
    _store.clear()
