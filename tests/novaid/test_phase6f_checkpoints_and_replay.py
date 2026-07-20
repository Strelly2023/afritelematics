from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
import pytest

from afritech.novaid.api import build_durable_authentication_router
from afritech.novaid.application import DurableAuthenticationService
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.webauthn_delivery import (
    CheckpointOutcome,
    WebAuthnCheckpointRepository,
    WebAuthnOutboxRepository,
)


def uid() -> str:
    return str(uuid4())


def test_checkpoint_repository_classifies_duplicate_stale_and_conflict(tmp_path) -> None:
    tenant, resource = uid(), uid()
    uow = NovaIDUnitOfWork(tmp_path / "checkpoints.db")
    repo = WebAuthnCheckpointRepository(uow)
    with uow:
        repo.create_checkpoint(
            consumer_name="consumer-a",
            tenant_id=tenant,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            event_version=2,
            last_event_id="event-2",
            last_stream_id="stream-1",
        )
    assert (
        repo.classify(
            consumer_name="consumer-a",
            tenant_id=tenant,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            event_version=2,
            event_id="event-2",
        )
        == CheckpointOutcome.DUPLICATE_EVENT
    )
    assert (
        repo.classify(
            consumer_name="consumer-a",
            tenant_id=tenant,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            event_version=1,
            event_id="event-1",
        )
        == CheckpointOutcome.STALE_EVENT
    )
    assert (
        repo.classify(
            consumer_name="consumer-a",
            tenant_id=tenant,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            event_version=2,
            event_id="event-3",
        )
        == CheckpointOutcome.VERSION_CONFLICT
    )
    assert (
        repo.classify(
            consumer_name="consumer-a",
            tenant_id=tenant,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            event_version=3,
            event_id="event-4",
        )
        == CheckpointOutcome.NEWER_EVENT
    )


def test_dead_letter_replay_requeues_and_rejects_stale_events(tmp_path) -> None:
    tenant, resource = uid(), uid()
    uow = NovaIDUnitOfWork(tmp_path / "replay.db")
    with uow:
        uow.create_tenant(tenant, "Replay tenant", datetime.now(UTC))
    repo = WebAuthnOutboxRepository(uow)
    with uow:
        event_id = repo.create_event(
            tenant_id=tenant,
            event_type="WEBAUTHN_CREDENTIAL_REVOKED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            resource_version=2,
            correlation_id=uid(),
            request_id=uid(),
            payload={"reason": "test"},
        )
        uow.connection.execute(
            "UPDATE novaid_webauthn_outbox SET status='DEAD_LETTER', dead_letter_reason='test' "
            "WHERE outbox_id=?",
            (event_id,),
        )
    replayed = repo.replay_dead_letter(
        event_id=event_id,
        tenant_id=tenant,
        reason="retry",
        actor_identity_id=uid(),
    )
    assert replayed["event_id"] == event_id
    row = uow.connection.execute(
        "SELECT status,dead_letter_reason FROM novaid_webauthn_outbox WHERE outbox_id=?",
        (event_id,),
    ).fetchone()
    assert row["status"] == "PENDING"
    assert row["dead_letter_reason"] is None
    with uow:
        stale = repo.create_event(
            tenant_id=tenant,
            event_type="WEBAUTHN_CREDENTIAL_REVOKED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            resource_version=2,
            correlation_id=uid(),
            request_id=uid(),
            payload={"reason": "stale"},
        )
        uow.connection.execute(
            "UPDATE novaid_webauthn_outbox SET status='DEAD_LETTER', dead_letter_reason='test' "
            "WHERE outbox_id=?",
            (stale,),
        )
        repo.create_event(
            tenant_id=tenant,
            event_type="WEBAUTHN_CREDENTIAL_REVOKED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=resource,
            resource_version=3,
            correlation_id=uid(),
            request_id=uid(),
            payload={"reason": "newer"},
        )
    with pytest.raises(ValueError, match="dead_letter_stale"):
        repo.replay_dead_letter(
            event_id=stale,
            tenant_id=tenant,
            reason="retry",
            actor_identity_id=uid(),
        )


def test_internal_dead_letter_replay_routes_appear_in_openapi(tmp_path) -> None:
    tenant = uid()
    uow = NovaIDUnitOfWork(tmp_path / "openapi.db")
    with uow:
        uow.create_tenant(tenant, "OpenAPI tenant", datetime.now(UTC))
    app = FastAPI()
    app.include_router(
        build_durable_authentication_router(
            DurableAuthenticationService(uow, pepper=b"openapi-pepper" * 3)
        )
    )
    paths = app.openapi()["paths"]
    assert "/v1/novaid/internal/webauthn/outbox/dead-letters" in paths
    assert "/v1/novaid/internal/webauthn/outbox/{event_id}/replay" in paths
