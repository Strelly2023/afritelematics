from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.application import DurableAuthenticationService
from afritech.novaid.application.authentication import AuthenticationError
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


@pytest.fixture
def runtime(tmp_path):
    store = NovaIDUnitOfWork(tmp_path / "auth.db")
    tenant = uid()
    with store:
        store.create_tenant(tenant, "Tenant", datetime.now(UTC))
    return tenant, store, DurableAuthenticationService(store, pepper=b"phase3-test-pepper" * 2)


def register_and_verify(tenant, service):
    result = service.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="register-1",
        correlation_id=uid(),
        request_id=uid(),
    )
    service.verify_identity(
        tenant_id=tenant,
        identity_id=result["identity_id"],
        challenge_id=result["challenge_id"],
        code=result["verification_code"],
        correlation_id=uid(),
        request_id=uid(),
    )
    return result


def test_registration_is_atomic_idempotent_and_verification_single_use(runtime) -> None:
    tenant, store, service = runtime
    first = service.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="register-1",
        correlation_id=uid(),
        request_id=uid(),
    )
    retry = service.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="register-1",
        correlation_id=uid(),
        request_id=uid(),
    )
    assert retry["identity_id"] == first["identity_id"]
    assert store.count("novaid_identities") == 1
    with pytest.raises(AuthenticationError, match="IDEMPOTENCY_CONFLICT"):
        service.register(
            tenant_id=tenant,
            email="other@example.com",
            password="a different strong password",
            idempotency_key="register-1",
            correlation_id=uid(),
            request_id=uid(),
        )
    service.verify_identity(
        tenant_id=tenant,
        identity_id=first["identity_id"],
        challenge_id=first["challenge_id"],
        code=first["verification_code"],
        correlation_id=uid(),
        request_id=uid(),
    )
    with pytest.raises(AuthenticationError, match="OTP_EXPIRED"):
        service.verify_identity(
            tenant_id=tenant,
            identity_id=first["identity_id"],
            challenge_id=first["challenge_id"],
            code=first["verification_code"],
            correlation_id=uid(),
            request_id=uid(),
        )


def test_pending_and_cross_tenant_authentication_are_generic(runtime) -> None:
    tenant, store, service = runtime
    service.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="register-1",
        correlation_id=uid(),
        request_id=uid(),
    )
    for attempted_tenant in (tenant, uid()):
        with pytest.raises(AuthenticationError, match="INVALID_CREDENTIALS"):
            service.authenticate(
                tenant_id=attempted_tenant,
                email="person@example.com",
                password="a strong registration password",
                correlation_id=uid(),
                request_id=uid(),
            )


def test_mfa_controls_session_activation_rotation_and_replay(runtime) -> None:
    tenant, store, service = runtime
    register_and_verify(tenant, service)
    login = service.authenticate(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        correlation_id=uid(),
        request_id=uid(),
    )
    assert login["outcome"] == "MFA_REQUIRED"
    tokens = service.complete_mfa(
        tenant_id=tenant,
        session_id=login["session_id"],
        challenge_id=login["challenge_id"],
        code=login["mfa_code"],
        correlation_id=uid(),
        request_id=uid(),
    )
    original = tokens["refresh_token"]
    replacement = service.refresh(
        tenant_id=tenant, presented_token=original, correlation_id=uid(), request_id=uid()
    )
    assert replacement != original
    with pytest.raises(AuthenticationError, match="TOKEN_REPLAY_DETECTED"):
        service.refresh(
            tenant_id=tenant, presented_token=original, correlation_id=uid(), request_id=uid()
        )
    with pytest.raises(AuthenticationError, match="SESSION_REVOKED"):
        service.refresh(
            tenant_id=tenant, presented_token=replacement, correlation_id=uid(), request_id=uid()
        )
    session = store.connection.execute(
        "SELECT status FROM novaid_authentication_sessions WHERE session_id=?",
        (login["session_id"],),
    ).fetchone()
    assert session["status"] == "REVOKED"
    persisted = " ".join(
        row[0]
        for row in store.connection.execute(
            "SELECT password_hash FROM novaid_password_credentials UNION ALL "
            "SELECT secret_hash FROM novaid_otp_challenges UNION ALL "
            "SELECT token_hash FROM novaid_refresh_tokens"
        )
    )
    assert "strong registration" not in persisted
    assert original not in persisted


def test_tenant_bound_challenge_and_refresh(runtime) -> None:
    tenant, store, service = runtime
    registration = service.register(
        tenant_id=tenant,
        email="person@example.com",
        password="a strong registration password",
        idempotency_key="register-1",
        correlation_id=uid(),
        request_id=uid(),
    )
    with pytest.raises(AuthenticationError, match="OTP_INVALID"):
        service.verify_identity(
            tenant_id=uid(),
            identity_id=registration["identity_id"],
            challenge_id=registration["challenge_id"],
            code=registration["verification_code"],
            correlation_id=uid(),
            request_id=uid(),
        )
