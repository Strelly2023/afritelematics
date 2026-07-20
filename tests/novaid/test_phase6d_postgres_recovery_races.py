# ruff: noqa: E501 -- integration fixtures keep PostgreSQL contracts visible.
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import os
from uuid import uuid4

import psycopg
import pytest

from afritech.novaid.application.recovery import (
    RecoveryCodeService,
    RecoveryError,
    TenantWebAuthnPolicyService,
)
from afritech.novaid.persistence.pool import NovaIDPostgresPool
from afritech.novaid.persistence.postgres import PostgresNovaIdUnitOfWork


DSN = os.getenv("NOVAID_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="PostgreSQL integration unavailable")
WORKERS = 2
ITERATIONS = 20
PEPPER = b"phase-6d-postgres-recovery-pepper-at-least-32"


def uid() -> str:
    return str(uuid4())


def seed(role: str = "MEMBER") -> tuple[str, str, str, str]:
    tenant, identity, membership, session, now = uid(), uid(), uid(), uid(), datetime.now(UTC)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
            "VALUES(%s,'Phase 6D','ACTIVE',%s,%s)",
            (tenant, now, now),
        )
        connection.execute(
            "INSERT INTO novaid_identities(identity_id,tenant_id,normalized_email,status,created_at,updated_at) "
            "VALUES(%s,%s,%s,'ACTIVE',%s,%s)",
            (identity, tenant, f"{identity}@example.com", now, now),
        )
        connection.execute(
            "INSERT INTO novaid_tenant_memberships(membership_id,tenant_id,identity_id,role,status,created_at,updated_at) "
            "VALUES(%s,%s,%s,%s,'ACTIVE',%s,%s)",
            (membership, tenant, identity, role, now, now),
        )
        connection.execute(
            "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,membership_id,"
            "authentication_time,authentication_strength,risk_score,status,created_at,last_seen_at,expires_at,"
            "authenticated_at,idle_expires_at,absolute_expires_at,step_up_expires_at,authentication_methods,security_version) "
            "VALUES(%s,%s,%s,%s,%s,'PHISHING_RESISTANT',0,'ACTIVE',%s,%s,%s,%s,%s,%s,%s,'[\"WEBAUTHN\"]',1)",
            (
                session,
                tenant,
                identity,
                membership,
                now,
                now,
                now,
                now + timedelta(hours=12),
                now,
                now + timedelta(minutes=30),
                now + timedelta(hours=12),
                now + timedelta(minutes=5),
            ),
        )
    return tenant, identity, membership, session


def test_recovery_code_consumption_race_twenty_iterations() -> None:
    pool = NovaIDPostgresPool(DSN, minimum_size=2, maximum_size=4)
    tenant, identity, _, session = seed()
    generator = RecoveryCodeService(PostgresNovaIdUnitOfWork(pool=pool), pepper=PEPPER)
    for _ in range(ITERATIONS):
        generated = generator.generate_codes(
            tenant_id=tenant, identity_id=identity, session_id=session, count=1
        )
        code = generated["codes"][0]

        def consume(_: int) -> str:
            service = RecoveryCodeService(PostgresNovaIdUnitOfWork(pool=pool), pepper=PEPPER)
            try:
                service.consume_code(tenant_id=tenant, identity_id=identity, code=code)
                return "USED"
            except RecoveryError:
                return "REJECTED"

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            outcomes = list(executor.map(consume, range(WORKERS)))
        assert sorted(outcomes) == ["REJECTED", "USED"]
    assert pool.created == pool.available
    pool.close()


def test_postgres_policy_version_conflict_is_rejected() -> None:
    tenant, identity, _, session = seed("SECURITY_ADMIN")
    service = TenantWebAuthnPolicyService(PostgresNovaIdUnitOfWork(DSN))
    created = service.set_policy(
        tenant_id=tenant,
        actor_identity_id=identity,
        session_id=session,
        policy={},
        expected_version=None,
        reason="initial policy",
    )
    assert created["version"] == 1
    with pytest.raises(RecoveryError, match="POLICY_VERSION_CONFLICT"):
        service.set_policy(
            tenant_id=tenant,
            actor_identity_id=identity,
            session_id=session,
            policy={},
            expected_version=0,
            reason="stale policy",
        )
