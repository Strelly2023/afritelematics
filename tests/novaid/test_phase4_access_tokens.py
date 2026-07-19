# ruff: noqa: E501
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.application import DurableAuthenticationService
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.revocation import ProcessLocalRevocationStore
from afritech.novaid.tokens import AccessTokenError, AccessTokenService


def uid() -> str:
    return str(uuid4())


def active_runtime(tmp_path):
    tenant = uid()
    store = NovaIDUnitOfWork(tmp_path / "tokens.db")
    with store:
        store.create_tenant(tenant, "Token tenant", datetime.now(UTC))
    auth = DurableAuthenticationService(store, pepper=b"phase4-pepper" * 3)
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
    return tenant, store, registration, login


def token_service(store, revocations=None, **overrides):
    return AccessTokenService(
        store,
        revocations or ProcessLocalRevocationStore(),
        signing_key=b"phase4-signing-key-for-tests-only!!",
        issuer=overrides.get("issuer", "novaid-test"),
        audience=overrides.get("audience", "novaid-clients"),
    )


def test_access_token_claims_and_durable_validation(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    service = token_service(store)
    token = service.issue(tenant, login["session_id"], registration["membership_id"])
    claims = service.validate(token, expected_tenant=tenant)
    assert claims["tenant_id"] == tenant
    assert claims["session_id"] == login["session_id"]
    assert claims["security_version"] == 1
    assert token not in str(
        store.connection.execute("SELECT metadata FROM novaid_security_events").fetchall()
    )


def test_security_version_and_revocation_invalidate_access_token(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    revocations = ProcessLocalRevocationStore()
    service = token_service(store, revocations)
    token = service.issue(tenant, login["session_id"], registration["membership_id"])
    with store:
        store.connection.execute(
            "UPDATE novaid_identities SET security_version=security_version+1 WHERE identity_id=? AND tenant_id=?",
            (registration["identity_id"], tenant),
        )
    with pytest.raises(AccessTokenError, match="INVALID_ACCESS_TOKEN"):
        service.validate(token, expected_tenant=tenant)
    fresh = service.issue(tenant, login["session_id"], registration["membership_id"])
    revocations.revoke_session(tenant, login["session_id"], datetime.max.replace(tzinfo=UTC))
    with pytest.raises(AccessTokenError, match="SESSION_REVOKED"):
        service.validate(fresh, expected_tenant=tenant)


def test_wrong_tenant_audience_and_signing_key_fail_closed(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    service = token_service(store)
    token = service.issue(tenant, login["session_id"], registration["membership_id"])
    with pytest.raises(AccessTokenError, match="TENANT_ACCESS_DENIED"):
        service.validate(token, expected_tenant=uid())
    with pytest.raises(AccessTokenError, match="INVALID_ACCESS_TOKEN"):
        token_service(store, issuer="other").validate(token, expected_tenant=tenant)
