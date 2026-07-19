from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.application import DurableAuthenticationService, PasswordLifecycleService
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.revocation import ProcessLocalRevocationStore


def uid() -> str:
    return str(uuid4())


def active_account(tmp_path):
    tenant = uid()
    store = NovaIDUnitOfWork(tmp_path / "passwords.db")
    with store:
        store.create_tenant(tenant, "Passwords", datetime.now(UTC))
    auth = DurableAuthenticationService(store, pepper=b"password-tests" * 3)
    registration = auth.register(
        tenant_id=tenant,
        email="person@example.com",
        password="the original strong password",
        idempotency_key="register",
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
    login = auth.authenticate(
        tenant_id=tenant,
        email="person@example.com",
        password="the original strong password",
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
    return tenant, store, auth, registration, login


def test_password_change_supersedes_history_and_revokes_sessions(tmp_path) -> None:
    tenant, store, auth, registration, login = active_account(tmp_path)
    passwords = PasswordLifecycleService(
        store, ProcessLocalRevocationStore(), pepper=b"password-reset" * 3
    )
    passwords.change(
        tenant_id=tenant,
        identity_id=registration["identity_id"],
        session_id=login["session_id"],
        current_password="the original strong password",
        new_password="the replacement strong password",
    )
    with pytest.raises(ValueError, match="INVALID_CREDENTIALS"):
        auth.authenticate(
            tenant_id=tenant,
            email="person@example.com",
            password="the original strong password",
            correlation_id=uid(),
            request_id=uid(),
        )
    second = auth.authenticate(
        tenant_id=tenant,
        email="person@example.com",
        password="the replacement strong password",
        correlation_id=uid(),
        request_id=uid(),
    )
    auth.complete_mfa(
        tenant_id=tenant,
        session_id=second["session_id"],
        challenge_id=second["challenge_id"],
        code=second["mfa_code"],
        correlation_id=uid(),
        request_id=uid(),
    )
    statuses = [
        row[0]
        for row in store.connection.execute(
            "SELECT status FROM novaid_credentials WHERE identity_id=? ORDER BY created_at",
            (registration["identity_id"],),
        )
    ]
    assert statuses == ["SUPERSEDED", "ACTIVE"]
    with pytest.raises(ValueError, match="PASSWORD_REUSE_REJECTED"):
        passwords.change(
            tenant_id=tenant,
            identity_id=registration["identity_id"],
            session_id=second["session_id"],
            current_password="the replacement strong password",
            new_password="the original strong password",
        )


def test_password_reset_is_generic_single_use_and_revokes_old_state(tmp_path) -> None:
    tenant, store, auth, registration, login = active_account(tmp_path)
    passwords = PasswordLifecycleService(
        store, ProcessLocalRevocationStore(), pepper=b"password-reset" * 3
    )
    assert passwords.request_reset(
        tenant_id=tenant, email="missing@example.com", correlation_id=uid()
    ) == {"status": "ACCEPTED"}
    reset = passwords.request_reset(
        tenant_id=tenant, email="person@example.com", correlation_id=uid()
    )
    passwords.complete_reset(
        tenant_id=tenant,
        challenge_id=reset["challenge_id"],
        code=reset["reset_code"],
        new_password="a reset replacement password",
    )
    with pytest.raises(ValueError, match="PASSWORD_RESET_REJECTED"):
        passwords.complete_reset(
            tenant_id=tenant,
            challenge_id=reset["challenge_id"],
            code=reset["reset_code"],
            new_password="another replacement password",
        )
    session = store.connection.execute(
        "SELECT status FROM novaid_authentication_sessions WHERE session_id=?",
        (login["session_id"],),
    ).fetchone()[0]
    assert session == "REVOKED"
    assert auth.authenticate(
        tenant_id=tenant,
        email="person@example.com",
        password="a reset replacement password",
        correlation_id=uid(),
        request_id=uid(),
    )
