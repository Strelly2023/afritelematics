from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from afritech.api.auth.jwt_device_auth import JWT
from afritech.api.novaid_audit_replay_api import build_novaid_audit_replay_router
from afritech.novaid.audit_replay import AuditReplayError, AuditReplayService
from afritech.novaid.domain.models import SecurityEvent
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def _seed_event(uow: NovaIDUnitOfWork, *, tenant_id: str, subject_id: str, event_type: str) -> str:
    event = SecurityEvent(
        event_id=uid(),
        event_type=event_type,
        severity="LOW",
        tenant_id=tenant_id,
        actor_identity_id=subject_id,
        subject_identity_id=subject_id,
        correlation_id=uid(),
        request_id=uid(),
        outcome="SUCCESS",
        reason_codes=("test",),
        metadata={"kind": "replay-test"},
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        schema_version=1,
    )
    uow.add_event(event)
    return event.event_id


def test_audit_replay_service_persists_request_execution_and_evidence(tmp_path) -> None:
    uow = NovaIDUnitOfWork(tmp_path / "replay.db")
    tenant = uid()
    with uow:
        uow.create_tenant(tenant, "Replay tenant", datetime.now(UTC))
        _seed_event(
            uow,
            tenant_id=tenant,
            subject_id=uid(),
            event_type="credential.webauthn.registered",
        )
        _seed_event(
            uow,
            tenant_id=tenant,
            subject_id=uid(),
            event_type="security.session.created",
        )

    service = AuditReplayService(uow)
    request = service.create_request(
        tenant_id=tenant,
        organization_id=tenant,
        requested_by=uid(),
        event_type_filters=["credential.webauthn.registered"],
        aggregate_filters={},
        subject_filters={},
        start_time=None,
        end_time=None,
        source_checkpoint=None,
        target_checkpoint=None,
        replay_mode="dry_run",
        dry_run=True,
        reason="investigate credential event",
        risk_level="moderate",
        maximum_events=10,
        correlation_id=uid(),
        request_id=uid(),
    )

    evaluation = service.evaluate(request["replay_request_id"])
    assert evaluation["matched_events"] == 1
    assert evaluation["required_approval"] is False

    evidence = service.execute(
        request["replay_request_id"], executor_id=uid(), reason="dry run complete"
    )
    assert evidence["status"] == "completed"
    package = service.evidence(request["replay_request_id"])
    assert package["counts"]["matched"] == 1
    assert package["counts"]["applied"] == 0
    assert package["counts"]["skipped"] == 1


def test_audit_replay_execution_failure_is_recorded(tmp_path) -> None:
    uow = NovaIDUnitOfWork(tmp_path / "failure.db")
    tenant = uid()
    with uow:
        uow.create_tenant(tenant, "Failure tenant", datetime.now(UTC))
    service = AuditReplayService(uow)
    request = service.create_request(
        tenant_id=tenant,
        organization_id=tenant,
        requested_by=uid(),
        event_type_filters=["credential.webauthn.registered"],
        aggregate_filters={},
        subject_filters={},
        start_time=None,
        end_time=None,
        source_checkpoint=None,
        target_checkpoint=None,
        replay_mode="dry_run",
        dry_run=True,
        reason="force failure",
        risk_level="moderate",
        maximum_events=10,
        correlation_id=uid(),
        request_id=uid(),
    )

    def broken_query(*args, **kwargs):  # noqa: ANN001, ANN002
        raise RuntimeError("boom")

    service._event_query = broken_query  # type: ignore[method-assign]

    with pytest.raises(AuditReplayError, match="replay_execution_failed"):
        service.execute(request["replay_request_id"], executor_id=uid(), reason="run")

    row = uow.connection.execute(
        "SELECT status FROM novaid_audit_replay_requests WHERE replay_request_id=?",
        (request["replay_request_id"],),
    ).fetchone()
    assert row["status"] == "failed"


def test_audit_replay_api_enforces_auth_and_permission_boundaries(tmp_path) -> None:
    uow = NovaIDUnitOfWork(tmp_path / "api.db")
    tenant = uid()
    with uow:
        uow.create_tenant(tenant, "API tenant", datetime.now(UTC))
        _seed_event(
            uow,
            tenant_id=tenant,
            subject_id=uid(),
            event_type="credential.webauthn.registered",
        )

    service = AuditReplayService(uow)
    app = FastAPI()
    app.include_router(build_novaid_audit_replay_router(service))
    client = TestClient(app)

    unauth = client.get("/api/v1/audit/replay/requests")
    assert unauth.status_code == 401
    assert unauth.headers["content-type"].startswith("application/json")

    read_only_token = JWT.create_token(
        "auditor",
        role="OBSERVER",
        organization_id=tenant,
        tenant_id=tenant,
        permissions=(
            "audit.events.read",
            "audit.events.read_sensitive",
            "audit.checkpoints.read",
            "audit.dead_letters.read",
            "audit.replay.evidence.read",
        ),
    )
    read_only_headers = {"Authorization": f"Bearer {read_only_token}"}
    forbidden = client.post(
        "/api/v1/audit/replay/requests",
        headers=read_only_headers,
        json={"reason": "blocked", "dry_run": True},
    )
    assert forbidden.status_code == 403

    admin_token = JWT.create_token(
        "security-admin",
        role="ADMIN",
        organization_id=tenant,
        tenant_id=tenant,
        permissions=(
            "audit.events.read",
            "audit.events.read_sensitive",
            "audit.events.export",
            "audit.checkpoints.read",
            "audit.dead_letters.read",
            "audit.replay.request",
            "audit.replay.approve",
            "audit.replay.execute",
            "audit.replay.cancel",
            "audit.replay.evidence.read",
        ),
    )
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/audit/replay/requests",
        headers=headers,
        json={
            "event_type_filters": ["credential.webauthn.registered"],
            "reason": "investigate",
            "dry_run": True,
            "replay_mode": "dry_run",
        },
    )
    assert created.status_code == 200, created.text
    replay_request_id = created.json()["replay_request_id"]

    events = client.get(
        f"/api/v1/audit/replay/requests/{replay_request_id}/events", headers=headers
    )
    assert events.status_code == 200
    assert len(events.json()) == 1

    approved = client.post(
        f"/api/v1/audit/replay/requests/{replay_request_id}/approve",
        headers={
            "Authorization": "Bearer "
            + JWT.create_token(
                "security-approver",
                role="ADMIN",
                organization_id=tenant,
                tenant_id=tenant,
                permissions=(
                    "audit.events.read",
                    "audit.events.read_sensitive",
                    "audit.events.export",
                    "audit.checkpoints.read",
                    "audit.dead_letters.read",
                    "audit.replay.approve",
                    "audit.replay.execute",
                    "audit.replay.evidence.read",
                ),
            )
        },
        json={"reason": "separate approval"},
    )
    assert approved.status_code == 200

    self_approval_request = client.post(
        "/api/v1/audit/replay/requests",
        headers=headers,
        json={
            "event_type_filters": ["credential.webauthn.registered"],
            "reason": "self approval check",
            "dry_run": True,
            "replay_mode": "dry_run",
        },
    )
    self_approval_id = self_approval_request.json()["replay_request_id"]
    self_approval = client.post(
        f"/api/v1/audit/replay/requests/{self_approval_id}/approve",
        headers=headers,
        json={"reason": "same actor"},
    )
    assert self_approval.status_code == 403

    executed = client.post(
        f"/api/v1/audit/replay/requests/{replay_request_id}/execute",
        headers=headers,
        json={"reason": "execute dry run"},
    )
    assert executed.status_code == 200

    evidence = client.get(
        f"/api/v1/audit/replay/requests/{replay_request_id}/evidence", headers=headers
    )
    assert evidence.status_code == 200
    assert evidence.json()["counts"]["matched"] == 1

    read_only_execute = client.post(
        f"/api/v1/audit/replay/requests/{replay_request_id}/execute",
        headers=read_only_headers,
        json={"reason": "not allowed"},
    )
    assert read_only_execute.status_code == 403

    other_tenant = uid()
    with uow:
        uow.create_tenant(other_tenant, "Other tenant", datetime.now(UTC))
    other_token = JWT.create_token(
        "other-observer",
        role="OBSERVER",
        organization_id=other_tenant,
        tenant_id=other_tenant,
        permissions=("audit.events.read", "audit.checkpoints.read"),
    )
    cross_tenant = client.get(
        f"/api/v1/audit/replay/requests/{replay_request_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_tenant.status_code == 403
