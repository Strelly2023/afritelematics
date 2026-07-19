from datetime import UTC, datetime, timedelta
import os

import pytest

from afritech.novaid.revocation import RedisRevocationStore


URL = os.getenv("NOVAID_TEST_REDIS_URL")
pytestmark = pytest.mark.skipif(not URL, reason="NOVAID_TEST_REDIS_URL unavailable")


def test_two_clients_observe_tenant_bound_revocation() -> None:
    redis = pytest.importorskip("redis")
    first = redis.Redis.from_url(URL, decode_responses=True)
    second = redis.Redis.from_url(URL, decode_responses=True)
    first.flushdb()
    writer, reader = RedisRevocationStore(first), RedisRevocationStore(second)
    expiry = datetime.now(UTC) + timedelta(minutes=5)
    writer.revoke_session("tenant-a", "session-a", expiry)
    writer.revoke_family("tenant-a", "family-a", expiry)
    assert reader.is_session_revoked("tenant-a", "session-a")
    assert reader.is_family_revoked("tenant-a", "family-a")
    assert not reader.is_session_revoked("tenant-b", "session-a")
    keys = second.keys("*")
    assert all("token" not in key and "password" not in key and "otp" not in key for key in keys)
    assert all(0 < second.ttl(key) <= 300 for key in keys)
