from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import os
from threading import Lock
from uuid import uuid4

import psycopg
import pytest

from afritech.novaid.application import DurableAuthenticationService
from afritech.novaid.outbox import RevocationOutbox
from afritech.novaid.persistence.pool import NovaIDPostgresPool
from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork
from afritech.novaid.revocation_delivery import RevocationPublisher


DSN = os.getenv("NOVAID_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="PostgreSQL integration unavailable")
ITERATIONS = 20
WORKERS = 2


def uid() -> str:
    return str(uuid4())


def seed_tenant() -> str:
    tenant, now = uid(), datetime.now(UTC)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,'Race','ACTIVE',%s,%s)",
            (tenant, now, now),
        )
    return tenant


def test_registration_idempotency_race_twenty_iterations() -> None:
    pool = NovaIDPostgresPool(DSN, minimum_size=2, maximum_size=4)
    for iteration in range(ITERATIONS):
        tenant, key = seed_tenant(), f"race-{iteration}"

        def register():
            service = DurableAuthenticationService(
                PostgresNovaIdUnitOfWork(pool=pool), pepper=b"phase-5e-race-pepper" * 3
            )
            return service.register(
                tenant_id=tenant,
                email="race@example.com",
                password="a strong race password",
                idempotency_key=key,
                correlation_id=uid(),
                request_id=uid(),
            )

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            results = list(executor.map(lambda _: register(), range(WORKERS)))
        assert results[0] == results[1]
        with psycopg.connect(DSN) as connection:
            counts = connection.execute(
                "SELECT (SELECT count(*) FROM novaid_identities WHERE tenant_id=%s),"
                "(SELECT count(*) FROM novaid_tenant_memberships WHERE tenant_id=%s),"
                "(SELECT count(*) FROM novaid_credentials WHERE tenant_id=%s),"
                "(SELECT count(*) FROM novaid_otp_challenges WHERE tenant_id=%s)",
                (tenant, tenant, tenant, tenant),
            ).fetchone()
        assert counts == (1, 1, 1, 1)
    assert pool.created == pool.available
    pool.close()


class ThreadSafeRedis:
    def __init__(self) -> None:
        self.messages, self.lock = [], Lock()

    def publish(self, channel, message):
        with self.lock:
            self.messages.append((channel, message))


def test_outbox_claim_race_twenty_iterations() -> None:
    pool, redis = NovaIDPostgresPool(DSN, minimum_size=2, maximum_size=4), ThreadSafeRedis()
    with psycopg.connect(DSN) as connection:
        connection.execute("DELETE FROM novaid_security_outbox")
    for iteration in range(ITERATIONS):
        tenant, resource = seed_tenant(), uid()
        seed_uow = PostgresNovaIdUnitOfWork(pool=pool)
        with seed_uow:
            RevocationOutbox(seed_uow).enqueue(
                tenant_id=tenant,
                event_type="SESSION_REVOKED",
                resource_type="SESSION",
                resource_id=resource,
                event_version=1,
                payload={"reason": "race"},
            )

        def publish(worker: int) -> int:
            uow = PostgresNovaIdUnitOfWork(pool=pool)
            return RevocationPublisher(
                RevocationOutbox(uow), redis, instance_id=f"publisher-{worker}"
            ).publish_once()

        before = len(redis.messages)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            published = list(executor.map(publish, range(WORKERS)))
        assert sum(published) == 1
        assert len(redis.messages) == before + 1
    assert pool.created == pool.available
    pool.close()
