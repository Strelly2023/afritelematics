"""Manual real-Redis outage/recovery certificate probe."""

from datetime import UTC, datetime, timedelta
import os
import sys
from uuid import uuid4

import psycopg
import redis

from afritech.novaid.outbox import RevocationOutbox
from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork
from afritech.novaid.revocation_delivery import RevocationConsumer, RevocationPublisher


dsn, redis_url, mode = (
    os.environ["NOVAID_TEST_DATABASE_URL"],
    os.environ["NOVAID_TEST_REDIS_URL"],
    sys.argv[1],
)
if mode == "prepare":
    tenant, resource, now = str(uuid4()), str(uuid4()), datetime.now(UTC)
    with psycopg.connect(dsn) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,'Redis Probe','ACTIVE',%s,%s)",
            (tenant, now, now),
        )
    uow = PostgresNovaIdUnitOfWork(dsn)
    with uow:
        RevocationOutbox(uow).enqueue(
            tenant_id=tenant,
            event_type="SESSION_REVOKED",
            resource_type="SESSION",
            resource_id=resource,
            event_version=1,
            payload={"reason": "phase5f_probe"},
        )
    uow.close()
    print("prepared")
elif mode == "fail":
    uow = PostgresNovaIdUnitOfWork(dsn)
    publisher = RevocationPublisher(
        RevocationOutbox(uow),
        redis.Redis.from_url(redis_url, decode_responses=True),
        instance_id="phase5f-failure",
    )
    assert publisher.publish_once() == 0
    row = uow.connection.execute(
        "SELECT status FROM novaid_security_outbox WHERE payload->>'reason'='phase5f_probe' "
        "ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row["status"] == "FAILED"
    print(f"outage_retained status=FAILED retries={publisher.retries}")
    uow.close()
elif mode == "recover":
    client, uow = (
        redis.Redis.from_url(redis_url, decode_responses=True),
        PostgresNovaIdUnitOfWork(dsn),
    )
    with uow:
        uow.connection.execute(
            "UPDATE novaid_security_outbox SET next_attempt_at=?,available_at=?,"
            "lease_expires_at=NULL "
            "WHERE payload->>'reason'='phase5f_probe' AND status='FAILED'",
            (
                (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
                (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            ),
        )
    publisher = RevocationPublisher(RevocationOutbox(uow), client, instance_id="phase5f-recovery")
    assert publisher.publish_once() >= 1
    client.flushdb()
    rebuilt = RevocationConsumer(client, uow=uow).rebuild_from_database()
    assert rebuilt > 0
    print(f"recovered published=1 rebuilt={rebuilt}")
    uow.close()
