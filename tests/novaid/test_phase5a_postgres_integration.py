# ruff: noqa: E501
from datetime import UTC, datetime
import os
from uuid import uuid4

import pytest

from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork


DSN = os.getenv("NOVAID_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="NOVAID_TEST_DATABASE_URL unavailable")


def uid() -> str:
    return str(uuid4())


def test_postgres_round_trip_tenant_isolation_and_row_locking() -> None:
    tenant, other, identity, now = uid(), uid(), uid(), datetime.now(UTC)
    with PostgresNovaIdUnitOfWork(DSN) as uow:
        uow.connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) VALUES(%s,%s,'ACTIVE',%s,%s)",
            (tenant, "Integration", now, now),
        )
        uow.connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) VALUES(%s,%s,'ACTIVE',%s,%s)",
            (other, "Other", now, now),
        )
        uow.connection.execute(
            "INSERT INTO novaid_identities(identity_id,tenant_id,normalized_email,status,created_at,updated_at) "
            "VALUES(%s,%s,%s,'ACTIVE',%s,%s)",
            (identity, tenant, f"{identity}@example.com", now, now),
        )
    with PostgresNovaIdUnitOfWork(DSN) as uow:
        assert (
            str(uow.identities.get_for_tenant(tenant, identity, lock=True)["identity_id"])
            == identity
        )
        assert uow.identities.get_for_tenant(other, identity) is None
        assert uow.identities.increment_security_version(tenant, identity, 1) == 2
        with pytest.raises(RuntimeError, match="CONCURRENCY_CONFLICT"):
            uow.identities.increment_security_version(tenant, identity, 1)


def test_postgres_uow_rolls_back_on_audit_failure() -> None:
    tenant, now = uid(), datetime.now(UTC)
    with pytest.raises(Exception):
        with PostgresNovaIdUnitOfWork(DSN) as uow:
            uow.connection.execute(
                "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) VALUES(%s,%s,'ACTIVE',%s,%s)",
                (tenant, "Rollback", now, now),
            )
            uow.connection.execute(
                "INSERT INTO novaid_security_events(event_id) VALUES(%s)", (uid(),)
            )
    with PostgresNovaIdUnitOfWork(DSN) as uow:
        assert (
            uow.connection.execute(
                "SELECT 1 FROM novaid_tenants WHERE tenant_id=%s", (tenant,)
            ).fetchone()
            is None
        )
