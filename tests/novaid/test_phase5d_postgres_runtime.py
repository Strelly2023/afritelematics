from datetime import UTC, datetime
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.novaid.runtime import build_default_durable_router
from afritech.novaid.outbox import RevocationOutbox
from afritech.novaid.persistence.pool import NovaIDPostgresPool, PoolExhausted
from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork


DSN = os.getenv("NOVAID_TEST_DATABASE_URL")
REDIS_URL = os.getenv("NOVAID_TEST_REDIS_URL")
pytestmark = pytest.mark.skipif(
    not DSN or not REDIS_URL, reason="integration infrastructure unavailable"
)


def uid() -> str:
    return str(uuid4())


def test_postgres_native_mounted_registration_authentication_and_pool_return(monkeypatch) -> None:
    tenant, now = uid(), datetime.now(UTC)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,%s,'ACTIVE',%s,%s)",
            (tenant, "Phase 5D", now, now),
        )
    monkeypatch.setenv("NOVAID_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("NOVAID_DATABASE_URL", DSN)
    monkeypatch.setenv("NOVAID_REDIS_URL", REDIS_URL)
    monkeypatch.setenv("NOVAID_SIGNING_KEY", "phase-5d-signing-key-with-enough-bytes")
    router = build_default_durable_router()
    pool = router.novaid_postgres_pool
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    headers = {
        "x-tenant-id": tenant,
        "idempotency-key": "phase-5d-register",
        "x-correlation-id": uid(),
        "x-request-id": uid(),
    }
    registration = client.post(
        "/v1/novaid/register",
        headers=headers,
        json={"email": "postgres@example.com", "password": "a strong postgres password"},
    )
    assert registration.status_code == 202, registration.text
    registered = registration.json()
    assert (
        client.post(
            "/v1/novaid/verify",
            headers=headers,
            json={
                "identity_id": registered["identity_id"],
                "challenge_id": registered["challenge_id"],
                "code": registered["verification_code"],
            },
        ).status_code
        == 204
    )
    login = client.post(
        "/v1/novaid/authenticate",
        headers=headers,
        json={"email": "postgres@example.com", "password": "a strong postgres password"},
    )
    assert login.status_code == 200, login.text
    pending = login.json()
    verified = client.post(
        "/v1/novaid/mfa/verify",
        headers=headers,
        json={
            "session_id": pending["session_id"],
            "challenge_id": pending["challenge_id"],
            "code": pending["mfa_code"],
        },
    )
    assert verified.status_code == 200, verified.text
    tokens = verified.json()
    protected = {**headers, "authorization": f"Bearer {tokens['access_token']}"}
    profile = client.get("/v1/novaid/me", headers=protected)
    assert profile.status_code == 200, profile.text
    assert profile.json()["identity_id"] == registered["identity_id"]
    assert client.get("/v1/novaid/sessions", headers=protected).status_code == 200
    assert client.post("/v1/novaid/logout", headers=protected).status_code == 200
    assert client.get("/v1/novaid/me", headers=protected).status_code == 401
    assert pool.created == pool.available
    pool.close()


def test_postgres_pool_returns_connections_after_commit_rollback_and_exception() -> None:
    pool = NovaIDPostgresPool(DSN, minimum_size=1, maximum_size=1, timeout=0.05)
    with PostgresNovaIdUnitOfWork(pool=pool) as uow:
        assert uow.connection.execute("SELECT 1 value").fetchone()["value"] == 1
    assert pool.available == 1
    with pytest.raises(RuntimeError, match="force rollback"):
        with PostgresNovaIdUnitOfWork(pool=pool):
            raise RuntimeError("force rollback")
    assert pool.available == 1
    held = pool.acquire()
    with pytest.raises(PoolExhausted):
        pool.acquire()
    pool.release(held)
    pool.close()


def test_postgres_revocation_outbox_is_durable_and_secret_rejecting() -> None:
    tenant, now = uid(), datetime.now(UTC)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,%s,'ACTIVE',%s,%s)",
            (tenant, "Outbox", now, now),
        )
    uow = PostgresNovaIdUnitOfWork(DSN)
    outbox = RevocationOutbox(uow)
    with pytest.raises(ValueError, match="secret_in_revocation_outbox"):
        outbox.enqueue(
            tenant_id=tenant,
            event_type="SESSION_REVOKED",
            resource_type="SESSION",
            resource_id=uid(),
            event_version=1,
            payload={"token": "forbidden"},
        )
    resource = uid()
    with uow:
        outbox_id = outbox.enqueue(
            tenant_id=tenant,
            event_type="SESSION_REVOKED",
            resource_type="SESSION",
            resource_id=resource,
            event_version=1,
            payload={"reason": "logout"},
        )
    assert any(row["outbox_id"] == outbox_id for row in outbox.pending())
    with uow:
        outbox.mark_failed(outbox_id, "redis_unavailable")
    with uow:
        outbox.mark_published(outbox_id)
    with psycopg.connect(DSN) as connection:
        row = connection.execute(
            "SELECT status,attempt_count,payload FROM novaid_security_outbox WHERE outbox_id=%s",
            (outbox_id,),
        ).fetchone()
    assert row[0] == "PUBLISHED"
    assert row[1] == 1
    assert "forbidden" not in str(row[2])
    uow.close()
