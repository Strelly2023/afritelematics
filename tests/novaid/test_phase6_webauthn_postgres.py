from datetime import UTC, datetime
import os
from uuid import uuid4

import psycopg
import pytest

from afritech.novaid.application.webauthn import WebAuthnService
from afritech.novaid.domain import AuthenticatorPolicy
from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork


DSN = os.getenv("NOVAID_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="PostgreSQL integration unavailable")


def uid() -> str:
    return str(uuid4())


def test_postgres_registration_and_authentication_challenges_are_tenant_bound() -> None:
    tenant, identity, membership, now = uid(), uid(), uid(), datetime.now(UTC)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,'WebAuthn PG','ACTIVE',%s,%s)",
            (tenant, now, now),
        )
        connection.execute(
            "INSERT INTO novaid_identities(identity_id,tenant_id,normalized_email,status,"
            "created_at,updated_at) VALUES(%s,%s,%s,'ACTIVE',%s,%s)",
            (identity, tenant, f"{identity}@example.com", now, now),
        )
        connection.execute(
            "INSERT INTO novaid_tenant_memberships(membership_id,tenant_id,identity_id,role,status,"
            "created_at,updated_at) VALUES(%s,%s,%s,'MEMBER','ACTIVE',%s,%s)",
            (membership, tenant, identity, now, now),
        )
    uow = PostgresNovaIdUnitOfWork(DSN)
    service = WebAuthnService(
        uow,
        AuthenticatorPolicy(
            rp_id="localhost", rp_name="NovaID PostgreSQL", origins=("http://localhost",)
        ),
    )
    registration = service.registration_options(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        user_name="postgres-passkey@example.com",
        correlation_id=uid(),
        request_id=uid(),
    )
    authentication = service.authentication_options(
        tenant_id=tenant,
        identity_id=identity,
        session_id=None,
        correlation_id=uid(),
        request_id=uid(),
    )
    assert registration["public_key"]["rp"]["id"] == "localhost"
    assert authentication["public_key"]["rpId"] == "localhost"
    with psycopg.connect(DSN) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM novaid_webauthn_registration_challenges "
                "WHERE tenant_id=%s AND identity_id=%s AND status='PENDING'",
                (tenant, identity),
            ).fetchone()[0]
            == 1
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM novaid_webauthn_authentication_challenges "
                "WHERE tenant_id=%s AND identity_id=%s AND status='PENDING'",
                (tenant, identity),
            ).fetchone()[0]
            == 1
        )
    uow.close()
