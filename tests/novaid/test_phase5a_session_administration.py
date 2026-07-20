from datetime import UTC, datetime, timedelta
from uuid import uuid4

from afritech.novaid.application import DurableAuthenticationService, SessionAdministrationService
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.revocation import ProcessLocalRevocationStore


def uid() -> str:
    return str(uuid4())


def test_session_listing_logout_and_logout_all(tmp_path) -> None:
    tenant, now = uid(), datetime.now(UTC)
    store = NovaIDUnitOfWork(tmp_path / "sessions.db")
    with store:
        store.create_tenant(tenant, "Sessions", now)
    auth = DurableAuthenticationService(store, pepper=b"session-tests" * 3)
    registration = auth.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="registration",
        correlation_id=uid(),
        request_id=uid(),
    )
    auth.verify_identity(
        tenant_id=tenant,
        identity_id=registration["identity_id"],
        challenge_id=registration["challenge_id"],
        code=registration["verification_code"],
        correlation_id=uid(),
        request_id=uid(),
    )
    sessions = []
    for _ in range(2):
        login = auth.authenticate(
            tenant_id=tenant,
            email="person@example.com",
            password="a strong registration password",
            correlation_id=uid(),
            request_id=uid(),
        )
        auth.complete_mfa(
            tenant_id=tenant,
            session_id=login["session_id"],
            challenge_id=login["challenge_id"],
            code=login["mfa_code"],
            correlation_id=uid(),
            request_id=uid(),
        )
        sessions.append(login["session_id"])
    revocations = ProcessLocalRevocationStore()
    service = SessionAdministrationService(store, revocations)
    assert len(service.list_own(tenant, registration["identity_id"])) == 2
    assert service.revoke(tenant, registration["identity_id"], sessions[0])
    assert not service.revoke(tenant, registration["identity_id"], sessions[0])
    assert revocations.is_session_revoked(tenant, sessions[0])
    assert service.logout_all(tenant, registration["identity_id"]) == 1
    assert revocations.is_session_revoked(tenant, sessions[1])
    version = store.connection.execute(
        "SELECT security_version FROM novaid_identities WHERE identity_id=?",
        (registration["identity_id"],),
    ).fetchone()[0]
    assert version == 2


def test_session_expiry_and_compromise(tmp_path) -> None:
    tenant, identity, session, now = uid(), uid(), uid(), datetime.now(UTC)
    store = NovaIDUnitOfWork(tmp_path / "expiry.db")
    with store:
        store.create_tenant(tenant, "Expiry", now)
        store.connection.execute(
            "INSERT INTO novaid_identities VALUES(?,?,?,?,?,?,?,?)",
            (
                identity,
                tenant,
                "expiry@example.com",
                "ACTIVE",
                now.isoformat(),
                now.isoformat(),
                1,
                1,
            ),
        )
        store.connection.execute(
            "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
            "authentication_time,authentication_strength,credential_id,device_reference,"
            "client_reference,risk_score,status,created_at,last_seen_at,expires_at,revoked_at,"
            "revocation_reason,version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                session,
                tenant,
                identity,
                now.isoformat(),
                "PASSWORD_OTP",
                None,
                None,
                None,
                0.1,
                "ACTIVE",
                now.isoformat(),
                now.isoformat(),
                (now + timedelta(seconds=1)).isoformat(),
                None,
                None,
                1,
            ),
        )
    service = SessionAdministrationService(store, ProcessLocalRevocationStore())
    assert service.expire_stale(tenant, now=now + timedelta(seconds=2)) == 1
    with store:
        store.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',expires_at=? "
            "WHERE session_id=?",
            ((now.replace(year=now.year + 1)).isoformat(), session),
        )
    service.mark_compromised(tenant, identity, session)
    assert (
        store.connection.execute(
            "SELECT status FROM novaid_authentication_sessions WHERE session_id=?", (session,)
        ).fetchone()[0]
        == "COMPROMISED"
    )
