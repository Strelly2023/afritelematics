from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from afritech.novaride_runtime.persistence.postgres.resilience_repository import (
    PostgresOfflineOperationRepository,
    PostgresResilienceOutboxRepository,
)


@dataclass
class FakeConnection:
    calls: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    async def execute(self, query: str, *args: Any) -> None:
        self.calls.append((query, args))

    async def fetchrow(self, query: str, *args: Any) -> None:
        self.calls.append((query, args))
        return None

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.calls.append((query, args))
        return []


@pytest.mark.anyio
async def test_postgres_offline_claim_uses_skip_locked_and_region_scope() -> None:
    connection = FakeConnection()
    repo = PostgresOfflineOperationRepository(connection)

    await repo.claim_pending(region_code="KE", limit=10)

    query, args = connection.calls[-1]
    assert "FOR UPDATE SKIP LOCKED" in query
    assert "region_code = $1" in query
    assert args == ("KE", 10)


@pytest.mark.anyio
async def test_resilience_outbox_claim_and_ack_are_retry_safe() -> None:
    connection = FakeConnection()
    repo = PostgresResilienceOutboxRepository(connection)

    await repo.claim_batch(worker_id="worker_1", limit=5)
    await repo.mark_published("outbox_1", broker_ack="ack")
    await repo.mark_failed("outbox_2", error="temporary", exhausted=False)

    claim_query = connection.calls[0][0]
    assert "FOR UPDATE SKIP LOCKED" in claim_query
    assert "state IN ('PENDING','FAILED')" in claim_query
    assert "PUBLISHED" in connection.calls[1][0]
    assert "DEAD_LETTERED" in connection.calls[2][0] or connection.calls[2][1][1] == "FAILED"
