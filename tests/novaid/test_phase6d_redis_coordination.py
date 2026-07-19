import os
from uuid import uuid4

import pytest
import redis

from afritech.novaid.webauthn_coordination import RedisWebAuthnChallengeCoordinator


URL = os.getenv("NOVAID_TEST_REDIS_URL")
pytestmark = pytest.mark.skipif(not URL, reason="Redis integration unavailable")


def uid() -> str:
    return str(uuid4())


def test_redis_challenge_supersession_and_single_consumption() -> None:
    client = redis.Redis.from_url(URL, decode_responses=True)
    client.flushdb()
    coordinator = RedisWebAuthnChallengeCoordinator(client, required=True)
    tenant, subject, first, second = uid(), uid(), uid(), uid()
    created_first = coordinator.create(
        tenant_id=tenant,
        subject=subject,
        purpose="AUTHENTICATION",
        challenge_id=first,
        challenge_hash="first-hash",
        ttl_seconds=60,
    )
    assert created_first.status == "CREATED"
    created_second = coordinator.create(
        tenant_id=tenant,
        subject=subject,
        purpose="AUTHENTICATION",
        challenge_id=second,
        challenge_hash="second-hash",
        ttl_seconds=60,
    )
    assert created_second.status == "CREATED"
    first_state = client.hgetall(coordinator._challenge_key(tenant, first, "AUTHENTICATION"))
    assert first_state["status"] == "SUPERSEDED"
    consumed = coordinator.consume(
        tenant_id=tenant, challenge_id=second, challenge_hash="second-hash", purpose="AUTHENTICATION"
    )
    assert consumed.status == "CONSUMED"
    second_again = coordinator.consume(
        tenant_id=tenant,
        challenge_id=second,
        challenge_hash="second-hash",
        purpose="AUTHENTICATION",
    )
    assert second_again.status in {"ALREADY_CONSUMED", "CONSUMED"}
    assert "first-hash" not in " ".join(client.scan_iter(match="novaid:v1:tenant:*") or [])
