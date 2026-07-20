from datetime import UTC, datetime
from uuid import uuid4

import pytest

from afritech.novaid.domain import (
    AuthenticationDecision,
    AuthenticationPolicy,
    Identity,
    IdentityStatus,
    RequestContext,
    SecurityEvent,
)
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def context(tenant: str, actor: str) -> RequestContext:
    return RequestContext(tenant, actor, uid(), uid(), uid(), "MFA")


def test_identity_state_machine_fails_closed() -> None:
    identity = Identity(uid(), uid(), "person@example.com")
    active = identity.transition(IdentityStatus.ACTIVE)
    disabled = active.transition(IdentityStatus.DISABLED)
    assert disabled.transition(IdentityStatus.DELETED).status is IdentityStatus.DELETED
    with pytest.raises(ValueError, match="INVALID_IDENTITY_TRANSITION"):
        identity.transition(IdentityStatus.SUSPENDED)


def test_normalized_persistence_tenant_isolation_concurrency_and_atomic_audit(tmp_path) -> None:
    now = datetime.now(UTC)
    tenant_a, tenant_b, actor = uid(), uid(), uid()
    identity = Identity(uid(), tenant_a, "USER@EXAMPLE.COM")
    store = NovaIDUnitOfWork(tmp_path / "core.db")
    with store:
        store.create_tenant(tenant_a, "A", now)
        store.create_tenant(tenant_b, "B", now)
        store.add_identity(identity)
    with store:
        loaded = store.get_identity(context(tenant_a, actor), identity.identity_id)
        assert loaded.normalized_email == "user@example.com"
        activated = loaded.transition(IdentityStatus.ACTIVE)
        store.update_identity(context(tenant_a, actor), activated, loaded.version)
        store.add_event(
            SecurityEvent(
                uid(),
                "IDENTITY_ACTIVATED",
                "INFO",
                tenant_a,
                actor,
                identity.identity_id,
                uid(),
                uid(),
                "SUCCESS",
            )
        )
    with pytest.raises(LookupError, match="TENANT_ACCESS_DENIED"):
        with store:
            store.get_identity(context(tenant_b, actor), identity.identity_id)
    with pytest.raises(RuntimeError, match="CONCURRENCY_CONFLICT"):
        with store:
            store.update_identity(context(tenant_a, actor), activated, 1)
    assert store.count("novaid_security_events") == 1


def test_audit_rejects_secret_metadata_and_rolls_back_mutation(tmp_path) -> None:
    now, tenant, actor = datetime.now(UTC), uid(), uid()
    store = NovaIDUnitOfWork(tmp_path / "audit.db")
    with pytest.raises(ValueError, match="SECRET_IN_SECURITY_EVENT"):
        with store:
            store.create_tenant(tenant, "Rollback", now)
            event = SecurityEvent(
                uid(),
                "AUTHENTICATION_FAILED",
                "HIGH",
                tenant,
                actor,
                actor,
                uid(),
                uid(),
                "DENIED",
                metadata={"password": "bad"},
            )
            store.add_event(event)
    assert store.count("novaid_tenants") == 0


@pytest.mark.parametrize(
    ("status", "membership", "credential", "risk", "strength", "expected"),
    [
        (IdentityStatus.ACTIVE, True, True, 0.1, "MFA", AuthenticationDecision.ALLOW),
        (IdentityStatus.ACTIVE, True, True, 0.1, "PASSWORD", AuthenticationDecision.REQUIRE_MFA),
        (IdentityStatus.ACTIVE, True, True, 0.7, "MFA", AuthenticationDecision.REQUIRE_STEP_UP),
        (IdentityStatus.ACTIVE, True, True, 0.95, "MFA", AuthenticationDecision.LOCK_IDENTITY),
        (IdentityStatus.SUSPENDED, True, True, 0.1, "MFA", AuthenticationDecision.DENY),
        (None, True, True, 0.1, "MFA", AuthenticationDecision.DENY),
    ],
)
def test_authentication_policy(status, membership, credential, risk, strength, expected) -> None:
    decision, reasons = AuthenticationPolicy().evaluate(
        identity_status=status,
        membership_active=membership,
        credential_active=credential,
        risk_score=risk,
        authentication_strength=strength,
    )
    assert decision is expected
    assert reasons
