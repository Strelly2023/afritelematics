from __future__ import annotations

import asyncio

from afritech.platform_runtime.adapters.nats import NatsJetStreamAdapter
from afritech.platform_runtime.models import InfrastructureKind, InfrastructureRequirement


def test_nats_adapter_returns_deterministic_plan_and_fallback_discovery() -> None:
    adapter = NatsJetStreamAdapter("nats://127.0.0.1:4222")
    requirement = InfrastructureRequirement(
        id="req-1",
        product_code="novafleet",
        kind=InfrastructureKind.EVENT_TOPIC,
        name="novatech.fleet.events",
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

    assert discovery.discovered is False
    assert discovery.mode == "UNAVAILABLE"
    assert plan.product_code == "novafleet"
    assert applied.success is False
    assert verified.success is False
    assert rolled_back.success is True
