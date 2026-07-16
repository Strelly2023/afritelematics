"""Idempotency helpers for API platform endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IdempotencyRecord:
    key: str
    request_hash: str
    response: Any


class IdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def get(self, key: str) -> IdempotencyRecord | None:
        return self._records.get(key)

    def put(self, key: str, request_hash: str, response: Any) -> IdempotencyRecord:
        record = IdempotencyRecord(key=key, request_hash=request_hash, response=response)
        self._records[key] = record
        return record
