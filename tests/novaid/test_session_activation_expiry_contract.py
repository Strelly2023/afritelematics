from datetime import UTC, datetime
from uuid import uuid4

from afritech.novaid.application.authentication import (
    DurableAuthenticationService,
)
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def test_mfa_activation_sets_future_idle_expiry() -> None:
    tenant_id = uid()
    store = NovaIDUnitOfWork()

    now = datetime.now(UTC).isoformat()

    with store:
        store.connection.execute(
            "INSERT INTO novaid_tenants("
            "tenant_id,name,status,created_at,updated_at,version"
            ") VALUES(?,?,?,?,?,1)",
            (
                tenant_id,
                "Session Activation Contract",
                "ACTIVE",
                now,
                now,
            ),
        )

    service = DurableAuthenticationService(
        store,
        pepper=b"session-activation-contract-pepper-value",
    )

    registration = service.register(
        tenant_id=tenant_id,
        email="activation-contract@example.com",
        password="a strong registration password",
        idempotency_key="activation-contract-registration",
        correlation_id=uid(),
        request_id=uid(),
    )

    service.verify_identity(
        tenant_id=tenant_id,
        identity_id=registration["identity_id"],
        challenge_id=registration["challenge_id"],
        code=registration["verification_code"],
        correlation_id=uid(),
        request_id=uid(),
    )

    login = service.authenticate(
        tenant_id=tenant_id,
        email="activation-contract@example.com",
        password="a strong registration password",
        correlation_id=uid(),
        request_id=uid(),
    )

    before_activation = datetime.now(UTC)

    service.complete_mfa(
        tenant_id=tenant_id,
        session_id=login["session_id"],
        challenge_id=login["challenge_id"],
        code=login["mfa_code"],
        correlation_id=uid(),
        request_id=uid(),
    )

    row = store.connection.execute(
        "SELECT status,authenticated_at,last_seen_at,"
        "idle_expires_at,pending_mfa_expires_at "
        "FROM novaid_authentication_sessions "
        "WHERE session_id=?",
        (login["session_id"],),
    ).fetchone()

    assert row is not None
    assert row["status"] == "ACTIVE"
    assert row["authenticated_at"] is not None
    assert row["last_seen_at"] is not None
    assert row["pending_mfa_expires_at"] is None

    idle_expires_at = datetime.fromisoformat(row["idle_expires_at"])

    assert idle_expires_at > before_activation
