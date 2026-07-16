from __future__ import annotations

import asyncio

from afritech.platform_runtime.adapters.redis import RedisAdapter
from afritech.platform_runtime.models import InfrastructureKind, InfrastructureRequirement


async def _fake_send(host: str, port: int, parts: list[str]) -> bytes:
    command = parts[0]
    if command == "PING":
        return b"+PONG\r\n"
    if command == "SET":
        return b"+OK\r\n"
    if command == "GET":
        return b"$1\r\n1\r\n"
    if command == "DEL":
        return b":1\r\n"
    return b"-ERR\r\n"


def test_redis_adapter_executes_resp_commands(monkeypatch) -> None:
    monkeypatch.setattr("afritech.platform_runtime.adapters.redis._send", _fake_send)
    adapter = RedisAdapter("redis://127.0.0.1:6379/0")
    requirement = InfrastructureRequirement(
        id="req-1",
        product_code="novafleet",
        kind=InfrastructureKind.REDIS_NAMESPACE,
        name="novafleet",
        required=True,
        configuration={},
        desired_state="ready",
        ownership="novafleet",
        region="AU",
    )
    discovery = asyncio.run(adapter.discover(requirement))
    plan = asyncio.run(adapter.plan(requirement))
    applied = asyncio.run(adapter.apply(plan))
    verified = asyncio.run(adapter.verify(requirement))
    rolled_back = asyncio.run(adapter.rollback(applied))

    assert discovery.discovered is True
    assert discovery.mode == "REAL"
    assert plan.product_code == "novafleet"
    assert applied.success is True
    assert verified.success is True
    assert rolled_back.success is True
