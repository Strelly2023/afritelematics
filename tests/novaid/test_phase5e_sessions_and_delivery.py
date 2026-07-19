from datetime import UTC, datetime, timedelta
import json
from uuid import uuid4

from afritech.novaid.application.sessions import SessionAdministrationService
from afritech.novaid.observability import NovaIDMetrics, NovaIDTracer
from afritech.novaid.outbox import RevocationOutbox
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.revocation import ProcessLocalRevocationStore
from afritech.novaid.revocation_delivery import RevocationConsumer, RevocationPublisher


def uid() -> str:
    return str(uuid4())


def seeded_session(tmp_path, *, status: str = "ACTIVE"):
    uow = NovaIDUnitOfWork(tmp_path / f"{uid()}.db")
    tenant, identity, session, now = uid(), uid(), uid(), datetime.now(UTC)
    with uow:
        uow.create_tenant(tenant, "Session lifecycle", now)
        uow.connection.execute(
            "INSERT INTO novaid_identities VALUES(?,?,?,?,?,?,?,?)",
            (
                identity,
                tenant,
                f"{identity}@example.com",
                "ACTIVE",
                now.isoformat(),
                now.isoformat(),
                1,
                1,
            ),
        )
        uow.connection.execute(
            "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
            "authentication_time,authentication_strength,risk_score,status,created_at,last_seen_at,"
            "expires_at,version,idle_expires_at,absolute_expires_at,pending_mfa_expires_at,"
            "authentication_methods,security_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                session,
                tenant,
                identity,
                now.isoformat(),
                "PASSWORD_OTP",
                0.1,
                status,
                now.isoformat(),
                now.isoformat(),
                (now + timedelta(hours=12)).isoformat(),
                1,
                (now + timedelta(minutes=30)).isoformat(),
                (now + timedelta(hours=12)).isoformat(),
                (now + timedelta(minutes=5)).isoformat() if status == "PENDING_MFA" else None,
                '["PASSWORD","OTP"]',
                1,
            ),
        )
    return uow, tenant, identity, session


def test_session_step_up_lock_unlock_and_compromise_are_terminal(tmp_path) -> None:
    uow, tenant, identity, session = seeded_session(tmp_path)
    metrics, tracer = NovaIDMetrics(), NovaIDTracer()
    service = SessionAdministrationService(
        uow, ProcessLocalRevocationStore(), metrics=metrics, tracer=tracer
    )
    service.require_step_up(
        tenant, identity, session, until=datetime.now(UTC) + timedelta(minutes=5)
    )
    service.complete_step_up(tenant, identity, session)
    service.lock(tenant, identity, session)
    service.unlock(tenant, identity, session)
    service.mark_compromised(tenant, identity, session)
    row = uow.connection.execute(
        "SELECT status,compromised_at FROM novaid_authentication_sessions WHERE session_id=?",
        (session,),
    ).fetchone()
    assert row["status"] == "COMPROMISED"
    assert row["compromised_at"]
    assert (
        uow.connection.execute(
            "SELECT status FROM novaid_security_outbox WHERE resource_id=?", (session,)
        ).fetchone()["status"]
        == "PENDING"
    )


def test_session_expiry_engine_classifies_pending_idle_step_up_and_absolute(tmp_path) -> None:
    uow, tenant, identity, active = seeded_session(tmp_path)
    now = datetime.now(UTC)
    sessions = [(active, "ACTIVE", "idle_expires_at", "IDLE_EXPIRY")]
    for status, column, reason in (
        ("PENDING_MFA", "pending_mfa_expires_at", "PENDING_MFA_EXPIRY"),
        ("STEP_UP_REQUIRED", "step_up_expires_at", "STEP_UP_EXPIRY"),
    ):
        session = uid()
        with uow:
            uow.connection.execute(
                "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
                "authentication_time,authentication_strength,risk_score,status,created_at,last_seen_at,"
                "expires_at,version,absolute_expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session,
                    tenant,
                    identity,
                    now.isoformat(),
                    "PASSWORD",
                    0.1,
                    status,
                    now.isoformat(),
                    now.isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    1,
                    (now + timedelta(hours=12)).isoformat(),
                ),
            )
            uow.connection.execute(
                f"UPDATE novaid_authentication_sessions SET {column}=? WHERE session_id=?",
                ((now - timedelta(seconds=1)).isoformat(), session),
            )
        sessions.append((session, status, column, reason))
    with uow:
        uow.connection.execute(
            "UPDATE novaid_authentication_sessions SET idle_expires_at=? WHERE session_id=?",
            ((now - timedelta(seconds=1)).isoformat(), active),
        )
    metrics, tracer = NovaIDMetrics(), NovaIDTracer()
    service = SessionAdministrationService(
        uow, ProcessLocalRevocationStore(), metrics=metrics, tracer=tracer
    )
    assert service.expire_stale(tenant, now=now) == 3
    for session, _, _, reason in sessions:
        row = uow.connection.execute(
            "SELECT status,revocation_reason FROM novaid_authentication_sessions "
            "WHERE session_id=?",
            (session,),
        ).fetchone()
        assert (row["status"], row["revocation_reason"]) == ("EXPIRED", reason)
    assert any(span.name == "novaid.session.expire" for span in tracer.spans)


class FakeRedis:
    def __init__(self, *, fail_publish: bool = False) -> None:
        self.values, self.messages, self.fail_publish = {}, [], fail_publish

    def set(self, key, value, **kwargs):
        self.values[key] = value

    def publish(self, channel, message):
        if self.fail_publish:
            raise ConnectionError("redis unavailable")
        self.messages.append((channel, message))


def test_outbox_publisher_retries_and_consumer_is_versioned_and_defensive(tmp_path) -> None:
    uow, tenant, _, session = seeded_session(tmp_path)
    outbox = RevocationOutbox(uow)
    with uow:
        outbox_id = outbox.enqueue(
            tenant_id=tenant,
            event_type="SESSION_REVOKED",
            resource_type="SESSION",
            resource_id=session,
            event_version=2,
            payload={"reason": "logout"},
        )
    failed = RevocationPublisher(outbox, FakeRedis(fail_publish=True), instance_id="failed")
    assert failed.publish_once() == 0
    with uow:
        uow.connection.execute(
            "UPDATE novaid_security_outbox SET available_at=?,next_attempt_at=NULL "
            "WHERE outbox_id=?",
            ((datetime.now(UTC) - timedelta(seconds=1)).isoformat(), outbox_id),
        )
    redis = FakeRedis()
    publisher = RevocationPublisher(outbox, redis, instance_id="recovered")
    assert publisher.publish_once() == 1
    consumer = RevocationConsumer(redis)
    raw = redis.messages[0][1]
    assert consumer.consume_message(raw)
    assert consumer.consume_message(raw)
    stale = json.loads(raw)
    stale["event_id"], stale["event_version"] = uid(), 1
    assert consumer.consume_message(json.dumps(stale))
    assert not consumer.consume_message("not json")
    key = f"novaid:revoked:{tenant}:session:{session}"
    assert redis.values[key] == "2"
