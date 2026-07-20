from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.application import (
    AuthenticationLockoutService,
    DurableAuthenticationService,
    LockoutPolicy,
)
from afritech.novaid.application.authentication import AuthenticationError
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def test_temporary_lockout_is_persistent_generic_and_tenant_bound(tmp_path) -> None:
    tenant, other = uid(), uid()
    store = NovaIDUnitOfWork(tmp_path / "lockout.db")
    with store:
        store.create_tenant(tenant, "Lockout", datetime.now(UTC))
        store.create_tenant(other, "Other", datetime.now(UTC))
    lockout = AuthenticationLockoutService(
        store, pepper=b"lockout-pepper" * 3, policy=LockoutPolicy(threshold=3, lock_seconds=60)
    )
    auth = DurableAuthenticationService(store, pepper=b"auth-pepper" * 3, lockout=lockout)
    registration = auth.register(
        tenant_id=tenant,
        email="person@example.com",
        password="the correct strong password",
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
    for _ in range(3):
        with pytest.raises(AuthenticationError, match="INVALID_CREDENTIALS"):
            auth.authenticate(
                tenant_id=tenant,
                email="person@example.com",
                password="wrong",
                correlation_id=uid(),
                request_id=uid(),
            )
    assert lockout.is_locked(tenant, "person@example.com")
    assert not lockout.is_locked(other, "person@example.com")
    with pytest.raises(AuthenticationError, match="INVALID_CREDENTIALS"):
        auth.authenticate(
            tenant_id=tenant,
            email="person@example.com",
            password="the correct strong password",
            correlation_id=uid(),
            request_id=uid(),
        )
    lockout.reset(tenant, "person@example.com")
    assert auth.authenticate(
        tenant_id=tenant,
        email="person@example.com",
        password="the correct strong password",
        correlation_id=uid(),
        request_id=uid(),
    )
