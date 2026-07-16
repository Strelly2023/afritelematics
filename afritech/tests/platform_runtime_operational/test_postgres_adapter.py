from __future__ import annotations

import asyncio

import pytest

from afritech.platform_runtime.adapters.postgres import PostgresProvisioningAdapter
from afritech.platform_runtime.errors import ProductProvisioningFailed
from afritech.platform_runtime.models import InfrastructureKind, InfrastructureRequirement


class _FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]] | None = None) -> None:
        self.rows = rows or []
        self.executed: list[tuple[str, tuple[object, ...] | None]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement, params=None):
        self.executed.append((str(statement), params))

    async def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class _FakeConn:
    def __init__(self, rows: list[tuple[object, ...]] | None = None) -> None:
        self.cursor_obj = _FakeCursor(rows)
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj

    async def commit(self):
        self.committed = True


async def _fake_connect_factory(rows: list[tuple[object, ...]] | None = None):
    return _FakeConn(rows)


def test_postgres_adapter_rejects_invalid_identifier() -> None:
    adapter = PostgresProvisioningAdapter("postgresql://example")
    requirement = InfrastructureRequirement(
        id="req-1",
        product_code="novafleet",
        kind=InfrastructureKind.POSTGRES_SCHEMA,
        name="Invalid-Name",
        required=True,
        configuration={},
        desired_state="ready",
        ownership="novafleet",
        region="AU",
    )
    with pytest.raises(ProductProvisioningFailed):
        asyncio.run(adapter.plan(requirement))


def test_postgres_adapter_executes_real_sql_paths(monkeypatch) -> None:
    fake = _FakeConn(rows=[("novafleet",), ("novafleet",)])

    async def fake_connect(*args, **kwargs):
        return fake

    monkeypatch.setattr("afritech.platform_runtime.adapters.postgres.psycopg.AsyncConnection.connect", fake_connect)
    adapter = PostgresProvisioningAdapter("postgresql://example")
    requirement = InfrastructureRequirement(
        id="req-1",
        product_code="novafleet",
        kind=InfrastructureKind.POSTGRES_SCHEMA,
        name="novafleet",
        required=True,
        configuration={},
        desired_state="ready",
        ownership="novafleet",
        region="AU",
    )
    plan = asyncio.run(adapter.plan(requirement))
    applied = asyncio.run(adapter.apply(plan))
    discovered = asyncio.run(adapter.discover(requirement))
    verified = asyncio.run(adapter.verify(requirement))

    assert plan.product_code == "novafleet"
    assert applied.success is True
    assert discovered.discovered is True
    assert discovered.mode == "REAL"
    assert verified.success is True
    assert fake.committed is True
    assert any("CREATE SCHEMA IF NOT EXISTS" in statement for statement, _ in fake.cursor_obj.executed)
