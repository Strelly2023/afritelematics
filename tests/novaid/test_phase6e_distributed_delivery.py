# ruff: noqa: E501 -- integration test keeps event contracts visible.
from datetime import UTC, datetime
import json
import os
from uuid import uuid4

import psycopg
import pytest
import redis

from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork
from afritech.novaid.webauthn_delivery import (
    WebAuthnDistributedEventConsumer,
    WebAuthnOutboxPublisher,
    WebAuthnOutboxRepository,
)


DSN, REDIS_URL = os.getenv("NOVAID_TEST_DATABASE_URL"), os.getenv("NOVAID_TEST_REDIS_URL")
pytestmark = pytest.mark.skipif(
    not DSN or not REDIS_URL, reason="distributed infrastructure unavailable"
)


def uid() -> str:
    return str(uuid4())


def test_stream_publisher_consumer_duplicate_and_stale_rejection() -> None:
    tenant, now = uid(), datetime.now(UTC)
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    client.flushdb()
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,'Phase 6E','ACTIVE',%s,%s)",
            (tenant, now, now),
        )
    uow = PostgresNovaIdUnitOfWork(DSN)
    repository = WebAuthnOutboxRepository(uow)
    with uow:
        event_id = repository.create_event(
            tenant_id=tenant,
            event_type="WEBAUTHN_CREDENTIAL_REVOKED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference="opaque-credential",
            resource_version=2,
            correlation_id=uid(),
            request_id=uid(),
            payload={"status": "REVOKED"},
        )
    publisher = WebAuthnOutboxPublisher(repository, client, instance_id="publisher-a")
    assert publisher.publish_once() == 1
    consumer = WebAuthnDistributedEventConsumer(client, consumer_name="consumer-b")
    assert consumer.consume_available() == 1
    assert consumer.consume_available() == 1
    assert consumer.duplicates == 1
    stale = {
        "event_id": uid(),
        "schema_version": 1,
        "event_type": "WEBAUTHN_CREDENTIAL_SUSPENDED",
        "tenant_id": tenant,
        "resource_type": "WEBAUTHN_CREDENTIAL",
        "resource_reference": "opaque-credential",
        "resource_version": 1,
    }
    assert consumer.apply(stale)
    assert consumer.stale == 1
    row = uow.connection.execute(
        "SELECT status FROM novaid_webauthn_outbox WHERE outbox_id=?", (event_id,)
    ).fetchone()
    assert row["status"] == "PUBLISHED"
    assert (
        client.hget(f"novaid:v1:state:{tenant}:WEBAUTHN_CREDENTIAL:opaque-credential", "event_type")
        == "WEBAUTHN_CREDENTIAL_REVOKED"
    )
    assert (
        json.loads(client.xrange(WebAuthnOutboxPublisher.STREAM)[0][1]["event"])["schema_version"]
        == 1
    )
    uow.close()
