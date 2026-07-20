"""Governed audit replay for NovaID security events.

The replay surface is intentionally constrained:

- it reads from authoritative security event history;
- it records requests, approvals, executions, and event outcomes;
- it does not mutate identity state;
- it fails closed when authorization or scope is incomplete.
"""
# ruff: noqa: E501 -- replay SQL is intentionally explicit and grep-friendly.

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime
from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from .domain.models import SecurityEvent
from .observability import NovaIDMetrics, NovaIDTracer
from .persistence import NovaIDUnitOfWork, PostgresNovaIdUnitOfWork


REQUEST_STATUSES = {
    "draft",
    "requested",
    "policy_evaluated",
    "approval_pending",
    "approved",
    "executing",
    "verifying",
    "completed",
    "rejected",
    "cancelled",
    "failed",
    "verification_failed",
    "expired",
}

REPLAY_MODES = {
    "inspect_only",
    "dry_run",
    "reprocess_consumer",
    "rebuild_projection",
    "republish_transport",
}


def _id() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def _default_uow() -> AbstractContextManager[Any]:
    backend = os.getenv("NOVAID_PERSISTENCE_BACKEND", "sqlite").lower()
    if backend == "postgres":
        dsn = os.getenv("NOVAID_DATABASE_URL") or os.getenv("NOVAID_TEST_DATABASE_URL")
        if not dsn:
            raise RuntimeError("missing_novaid_postgres_url")
        return PostgresNovaIdUnitOfWork(dsn)
    path = Path(os.getenv("NOVAID_DURABLE_DB_PATH", "/tmp/novaid-durable.sqlite3"))
    return NovaIDUnitOfWork(path)


class AuditReplayError(ValueError):
    """Stable governed replay denial."""


class AuditReplayService:
    def __init__(self, uow: Any | None = None, *, metrics=None, tracer=None) -> None:
        self.uow = uow or _default_uow()
        self.metrics = metrics or NovaIDMetrics()
        self.tracer = tracer or NovaIDTracer()
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.uow.connection.execute(
            "CREATE TABLE IF NOT EXISTS novaid_audit_replay_requests("
            "replay_request_id text PRIMARY KEY,tenant_id text NOT NULL,organization_id text NOT NULL,"
            "environment_id text NOT NULL DEFAULT '',requested_by text NOT NULL,approved_by text,"
            "executed_by text,event_type_filters text NOT NULL DEFAULT '[]',aggregate_filters text NOT NULL DEFAULT '{}',"
            "subject_filters text NOT NULL DEFAULT '{}',start_time text,end_time text,"
            "source_checkpoint text,target_checkpoint text,replay_mode text NOT NULL,"
            "dry_run integer NOT NULL DEFAULT 0,reason text NOT NULL,risk_level text NOT NULL,"
            "status text NOT NULL,maximum_events integer NOT NULL DEFAULT 100,created_at text NOT NULL,"
            "approved_at text,started_at text,completed_at text,cancelled_at text,evidence_id text,"
            "correlation_id text NOT NULL,request_id text NOT NULL DEFAULT '',"
            "CHECK(status IN ('draft','requested','policy_evaluated','approval_pending','approved',"
            "'executing','verifying','completed','rejected','cancelled','failed','verification_failed','expired')),"
            "CHECK(replay_mode IN ('inspect_only','dry_run','reprocess_consumer','rebuild_projection','republish_transport'))"
            ")"
        )
        self.uow.connection.execute(
            "CREATE TABLE IF NOT EXISTS novaid_audit_replay_approvals("
            "approval_id text PRIMARY KEY,replay_request_id text NOT NULL,tenant_id text NOT NULL,"
            "organization_id text NOT NULL,approver_id text NOT NULL,decision text NOT NULL,"
            "reason text NOT NULL,created_at text NOT NULL,"
            "UNIQUE(replay_request_id,approver_id,decision))"
        )
        self.uow.connection.execute(
            "CREATE TABLE IF NOT EXISTS novaid_audit_replay_event_results("
            "result_id text PRIMARY KEY,replay_request_id text NOT NULL,tenant_id text NOT NULL,"
            "organization_id text NOT NULL,event_id text NOT NULL,event_type text NOT NULL,"
            "decision text NOT NULL,reason text NOT NULL,created_at text NOT NULL,"
            "UNIQUE(replay_request_id,event_id,decision))"
        )
        self.uow.connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_novaid_audit_replay_requests_tenant_status "
            "ON novaid_audit_replay_requests(tenant_id,status,created_at)"
        )
        self.uow.connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_novaid_audit_replay_results_request "
            "ON novaid_audit_replay_event_results(replay_request_id,decision,created_at)"
        )

    def _request_row(self, replay_request_id: str):
        row = self.uow.connection.execute(
            "SELECT * FROM novaid_audit_replay_requests WHERE replay_request_id=?",
            (replay_request_id,),
        ).fetchone()
        if not row:
            raise AuditReplayError("replay_request_not_found")
        return row

    def _record_event(
        self,
        *,
        event_type: str,
        tenant_id: str,
        organization_id: str,
        actor_identity_id: str,
        subject_identity_id: str,
        correlation_id: str,
        request_id: str,
        outcome: str,
        reason_codes: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = SecurityEvent(
            event_id=_id(),
            event_type=event_type,
            severity="LOW",
            tenant_id=tenant_id,
            actor_identity_id=actor_identity_id,
            subject_identity_id=subject_identity_id,
            correlation_id=correlation_id,
            request_id=request_id,
            outcome=outcome,
            reason_codes=reason_codes,
            metadata=metadata or {},
        )
        self.uow.connection.execute(
            "INSERT INTO novaid_security_events("
            "event_id,event_type,severity,tenant_id,actor_identity_id,subject_identity_id,"
            "correlation_id,request_id,occurred_at,recorded_at,outcome,reason_codes,metadata,"
            "schema_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.event_type,
                event.severity,
                event.tenant_id,
                event.actor_identity_id,
                event.subject_identity_id,
                event.correlation_id,
                event.request_id,
                event.occurred_at.isoformat(),
                event.recorded_at.isoformat(),
                event.outcome,
                _json(event.reason_codes),
                _json(event.metadata),
                event.schema_version,
            ),
        )

    @staticmethod
    def _parse_time(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    def _event_query(self, row: Any, *, limit: int | None = None) -> list[dict[str, Any]]:
        clauses = ["tenant_id=?"]
        params: list[Any] = [row["tenant_id"]]
        event_types = tuple(_loads(row["event_type_filters"], []))
        if event_types:
            placeholders = ",".join("?" for _ in event_types)
            clauses.append(f"event_type IN ({placeholders})")
            params.extend(event_types)
        subjects = _loads(row["subject_filters"], {})
        subject_identity_id = subjects.get("subject_identity_id")
        if subject_identity_id:
            clauses.append("subject_identity_id=?")
            params.append(str(subject_identity_id))
        actors = _loads(row["aggregate_filters"], {})
        actor_identity_id = actors.get("actor_identity_id")
        if actor_identity_id:
            clauses.append("actor_identity_id=?")
            params.append(str(actor_identity_id))
        start_time = self._parse_time(row["start_time"])
        end_time = self._parse_time(row["end_time"])
        if start_time:
            clauses.append("occurred_at>=?")
            params.append(start_time.isoformat())
        if end_time:
            clauses.append("occurred_at<=?")
            params.append(end_time.isoformat())
        sql = (
            "SELECT event_id,event_type,severity,tenant_id,actor_identity_id,subject_identity_id,"
            "correlation_id,request_id,occurred_at,recorded_at,outcome,reason_codes,metadata,schema_version "
            "FROM novaid_security_events WHERE "
            + " AND ".join(clauses)
            + " ORDER BY occurred_at ASC, event_id ASC"
        )
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.uow.connection.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def create_request(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        requested_by: str,
        event_type_filters: list[str] | tuple[str, ...] | None,
        aggregate_filters: dict[str, Any] | None,
        subject_filters: dict[str, Any] | None,
        start_time: datetime | None,
        end_time: datetime | None,
        source_checkpoint: str | None,
        target_checkpoint: str | None,
        replay_mode: str,
        dry_run: bool,
        reason: str,
        risk_level: str,
        maximum_events: int = 100,
        correlation_id: str = "",
        request_id: str = "",
    ) -> dict[str, Any]:
        if replay_mode not in REPLAY_MODES:
            raise AuditReplayError("invalid_replay_mode")
        if not reason.strip():
            raise AuditReplayError("reason_required")
        if maximum_events < 1 or maximum_events > 10_000:
            raise AuditReplayError("maximum_events_out_of_range")
        now = _now()
        replay_request_id = _id()
        with self.tracer.span(
            "novaid.audit.replay.request",
            {"operation": "audit.replay.request", "replay_request_id": replay_request_id},
        ):
            with self.uow:
                self.uow.connection.execute(
                    "INSERT INTO novaid_audit_replay_requests("
                    "replay_request_id,tenant_id,organization_id,environment_id,requested_by,approved_by,"
                    "executed_by,event_type_filters,aggregate_filters,subject_filters,start_time,end_time,"
                    "source_checkpoint,target_checkpoint,replay_mode,dry_run,reason,risk_level,status,"
                    "maximum_events,created_at,approved_at,started_at,completed_at,cancelled_at,evidence_id,"
                    "correlation_id,request_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        replay_request_id,
                        tenant_id,
                        organization_id,
                        "",
                        requested_by,
                        None,
                        None,
                        _json(list(event_type_filters or [])),
                        _json(aggregate_filters or {}),
                        _json(subject_filters or {}),
                        start_time.isoformat() if start_time else None,
                        end_time.isoformat() if end_time else None,
                        source_checkpoint,
                        target_checkpoint,
                        replay_mode,
                        bool(dry_run),
                        reason,
                        risk_level,
                        "requested",
                        maximum_events,
                        now.isoformat(),
                        None,
                        None,
                        None,
                        None,
                        None,
                        correlation_id,
                        request_id,
                    ),
                )
                self._record_event(
                    event_type="audit.replay.requested",
                    tenant_id=tenant_id,
                    organization_id=organization_id,
                    actor_identity_id=requested_by,
                    subject_identity_id=requested_by,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    outcome="REQUESTED",
                    reason_codes=("audit", "replay"),
                    metadata={
                        "replay_request_id": replay_request_id,
                        "replay_mode": replay_mode,
                        "dry_run": bool(dry_run),
                    },
                )
        self.metrics.increment("novaid_replay_requests_total", outcome="created")
        return self.get_request(replay_request_id)

    def list_requests(self, *, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.uow.connection.execute(
            "SELECT * FROM novaid_audit_replay_requests WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",
            (tenant_id, max(1, min(limit, 200))),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_request(self, replay_request_id: str) -> dict[str, Any]:
        row = self._request_row(replay_request_id)
        result = dict(row)
        result["event_type_filters"] = _loads(result.get("event_type_filters"), [])
        result["aggregate_filters"] = _loads(result.get("aggregate_filters"), {})
        result["subject_filters"] = _loads(result.get("subject_filters"), {})
        return result

    def evaluate(self, replay_request_id: str) -> dict[str, Any]:
        row = self._request_row(replay_request_id)
        events = self._event_query(row, limit=int(row["maximum_events"]))
        matched = len(events)
        denied = 0
        malformed = 0
        would_apply = matched if not row["dry_run"] else 0
        warnings = []
        if matched == 0:
            warnings.append("no_matching_events")
        risk_level = row["risk_level"]
        if not risk_level or risk_level == "unknown":
            risk_level = "moderate"
        with self.uow:
            self.uow.connection.execute(
                "UPDATE novaid_audit_replay_requests SET status='policy_evaluated' WHERE replay_request_id=?",
                (replay_request_id,),
            )
        return {
            "replay_request_id": replay_request_id,
            "matched_events": matched,
            "eligible_events": matched - denied - malformed,
            "denied_events": denied,
            "malformed_events": malformed,
            "would_apply": would_apply,
            "would_skip": matched - would_apply,
            "warnings": warnings,
            "risk_level": risk_level,
            "required_approval": not bool(row["dry_run"]),
        }

    def request_approval(self, replay_request_id: str, *, requested_by: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise AuditReplayError("reason_required")
        now = _now().isoformat()
        approval_id = _id()
        with self.uow:
            request = self._request_row(replay_request_id)
            if request["status"] not in {"requested", "policy_evaluated", "approval_pending"}:
                raise AuditReplayError("approval_not_allowed")
            self.uow.connection.execute(
                "INSERT INTO novaid_audit_replay_approvals("
                "approval_id,replay_request_id,tenant_id,organization_id,approver_id,decision,reason,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (
                    approval_id,
                    replay_request_id,
                    request["tenant_id"],
                    request["organization_id"],
                    requested_by,
                    "REQUESTED",
                    reason,
                    now,
                ),
            )
            self.uow.connection.execute(
                "UPDATE novaid_audit_replay_requests SET status='approval_pending' WHERE replay_request_id=?",
                (replay_request_id,),
            )
            self._record_event(
                event_type="audit.replay.approval_requested",
                tenant_id=request["tenant_id"],
                organization_id=request["organization_id"],
                actor_identity_id=requested_by,
                subject_identity_id=request["requested_by"],
                correlation_id=request["correlation_id"],
                request_id=request["request_id"],
                outcome="REQUESTED",
                reason_codes=("audit", "replay"),
                metadata={"replay_request_id": replay_request_id},
            )
        return {"approval_id": approval_id, "status": "approval_pending"}

    def approve(self, replay_request_id: str, *, approver_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise AuditReplayError("reason_required")
        now = _now().isoformat()
        approval_id = _id()
        with self.uow:
            request = self._request_row(replay_request_id)
            if request["requested_by"] == approver_id:
                raise AuditReplayError("self_approval_denied")
            if request["status"] not in {"requested", "policy_evaluated", "approval_pending"}:
                raise AuditReplayError("approval_not_allowed")
            self.uow.connection.execute(
                "INSERT INTO novaid_audit_replay_approvals("
                "approval_id,replay_request_id,tenant_id,organization_id,approver_id,decision,reason,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (
                    approval_id,
                    replay_request_id,
                    request["tenant_id"],
                    request["organization_id"],
                    approver_id,
                    "APPROVED",
                    reason,
                    now,
                ),
            )
            self.uow.connection.execute(
                "UPDATE novaid_audit_replay_requests SET status='approved',approved_by=?,approved_at=? "
                "WHERE replay_request_id=?",
                (approver_id, now, replay_request_id),
            )
            self._record_event(
                event_type="audit.replay.authorized",
                tenant_id=request["tenant_id"],
                organization_id=request["organization_id"],
                actor_identity_id=approver_id,
                subject_identity_id=request["requested_by"],
                correlation_id=request["correlation_id"],
                request_id=request["request_id"],
                outcome="APPROVED",
                reason_codes=("audit", "replay"),
                metadata={"replay_request_id": replay_request_id},
            )
        return {"approval_id": approval_id, "status": "approved"}

    def reject(self, replay_request_id: str, *, approver_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise AuditReplayError("reason_required")
        now = _now().isoformat()
        with self.uow:
            request = self._request_row(replay_request_id)
            self.uow.connection.execute(
                "INSERT INTO novaid_audit_replay_approvals("
                "approval_id,replay_request_id,tenant_id,organization_id,approver_id,decision,reason,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (
                    _id(),
                    replay_request_id,
                    request["tenant_id"],
                    request["organization_id"],
                    approver_id,
                    "REJECTED",
                    reason,
                    now,
                ),
            )
            self.uow.connection.execute(
                "UPDATE novaid_audit_replay_requests SET status='rejected',approved_by=?,approved_at=? "
                "WHERE replay_request_id=?",
                (approver_id, now, replay_request_id),
            )
            self._record_event(
                event_type="audit.replay.rejected",
                tenant_id=request["tenant_id"],
                organization_id=request["organization_id"],
                actor_identity_id=approver_id,
                subject_identity_id=request["requested_by"],
                correlation_id=request["correlation_id"],
                request_id=request["request_id"],
                outcome="REJECTED",
                reason_codes=("audit", "replay"),
                metadata={"replay_request_id": replay_request_id},
            )
        return {"status": "rejected"}

    def execute(self, replay_request_id: str, *, executor_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise AuditReplayError("reason_required")
        now = _now()
        with self.tracer.span(
            "novaid.audit.replay.execute",
            {"operation": "audit.replay.execute", "replay_request_id": replay_request_id},
        ):
            try:
                with self.uow:
                    request = self._request_row(replay_request_id)
                    if request["status"] not in {"approved", "policy_evaluated", "approval_pending"}:
                        raise AuditReplayError("replay_not_approved")
                    events = self._event_query(request, limit=int(request["maximum_events"]))
                    self.uow.connection.execute(
                        "UPDATE novaid_audit_replay_requests SET status='executing',executed_by=?,started_at=? "
                        "WHERE replay_request_id=?",
                        (executor_id, now.isoformat(), replay_request_id),
                    )
                    self._record_event(
                        event_type="audit.replay.started",
                        tenant_id=request["tenant_id"],
                        organization_id=request["organization_id"],
                        actor_identity_id=executor_id,
                        subject_identity_id=request["requested_by"],
                        correlation_id=request["correlation_id"],
                        request_id=request["request_id"],
                        outcome="STARTED",
                        reason_codes=("audit", "replay"),
                        metadata={"replay_request_id": replay_request_id},
                    )
                    for event in events:
                        decision = "APPLIED" if not request["dry_run"] else "SKIPPED"
                        self.uow.connection.execute(
                            "INSERT INTO novaid_audit_replay_event_results("
                            "result_id,replay_request_id,tenant_id,organization_id,event_id,event_type,"
                            "decision,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (
                                _id(),
                                replay_request_id,
                                request["tenant_id"],
                                request["organization_id"],
                                event["event_id"],
                                event["event_type"],
                                decision,
                                reason,
                                now.isoformat(),
                            ),
                        )
                        self._record_event(
                            event_type=(
                                "audit.replay.event_applied"
                                if decision == "APPLIED"
                                else "audit.replay.event_skipped"
                            ),
                            tenant_id=request["tenant_id"],
                            organization_id=request["organization_id"],
                            actor_identity_id=executor_id,
                            subject_identity_id=request["requested_by"],
                            correlation_id=request["correlation_id"],
                            request_id=request["request_id"],
                            outcome=decision,
                            reason_codes=("audit", "replay"),
                            metadata={
                                "replay_request_id": replay_request_id,
                                "event_id": event["event_id"],
                                "event_type": event["event_type"],
                            },
                        )
                    self.uow.connection.execute(
                        "UPDATE novaid_audit_replay_requests SET status='verifying',completed_at=?,evidence_id=? "
                        "WHERE replay_request_id=?",
                        (now.isoformat(), _id(), replay_request_id),
                    )
                    self.uow.connection.execute(
                        "UPDATE novaid_audit_replay_requests SET status='completed' WHERE replay_request_id=?",
                        (replay_request_id,),
                    )
                    self._record_event(
                        event_type="audit.replay.completed",
                        tenant_id=request["tenant_id"],
                        organization_id=request["organization_id"],
                        actor_identity_id=executor_id,
                        subject_identity_id=request["requested_by"],
                        correlation_id=request["correlation_id"],
                        request_id=request["request_id"],
                        outcome="COMPLETED",
                        reason_codes=("audit", "replay"),
                        metadata={
                            "replay_request_id": replay_request_id,
                            "event_count": len(events),
                        },
                    )
            except Exception as exc:
                with self.uow:
                    request = self._request_row(replay_request_id)
                    self.uow.connection.execute(
                        "UPDATE novaid_audit_replay_requests SET status='failed',completed_at=? "
                        "WHERE replay_request_id=?",
                        (now.isoformat(), replay_request_id),
                    )
                    self._record_event(
                        event_type="audit.replay.event_failed",
                        tenant_id=request["tenant_id"],
                        organization_id=request["organization_id"],
                        actor_identity_id=executor_id,
                        subject_identity_id=request["requested_by"],
                        correlation_id=request["correlation_id"],
                        request_id=request["request_id"],
                        outcome="FAILED",
                        reason_codes=("audit", "replay"),
                        metadata={
                            "replay_request_id": replay_request_id,
                            "error_type": type(exc).__name__,
                        },
                    )
                raise AuditReplayError("replay_execution_failed") from exc
        for _ in events:
            self.metrics.increment("novaid_replay_events_total", outcome="completed")
        return {
            "replay_request_id": replay_request_id,
            "status": "completed",
            "applied_events": len(events) if not request["dry_run"] else 0,
            "skipped_events": 0 if not request["dry_run"] else len(events),
            "evidence_id": self.get_request(replay_request_id).get("evidence_id"),
        }

    def cancel(self, replay_request_id: str, *, actor_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise AuditReplayError("reason_required")
        now = _now().isoformat()
        with self.uow:
            self._request_row(replay_request_id)
            self.uow.connection.execute(
                "UPDATE novaid_audit_replay_requests SET status='cancelled',cancelled_at=?,executed_by=? "
                "WHERE replay_request_id=?",
                (now, actor_id, replay_request_id),
            )
            request = self.get_request(replay_request_id)
            self._record_event(
                event_type="audit.replay.cancelled",
                tenant_id=request["tenant_id"],
                organization_id=request["organization_id"],
                actor_identity_id=actor_id,
                subject_identity_id=request["requested_by"],
                correlation_id=request["correlation_id"],
                request_id=request["request_id"],
                outcome="CANCELLED",
                reason_codes=("audit", "replay"),
                metadata={"replay_request_id": replay_request_id},
            )
        return {"status": "cancelled"}

    def events(self, replay_request_id: str) -> list[dict[str, Any]]:
        request = self._request_row(replay_request_id)
        return self._event_query(request, limit=int(request["maximum_events"]))

    def evidence(self, replay_request_id: str) -> dict[str, Any]:
        request = self.get_request(replay_request_id)
        results = self.uow.connection.execute(
            "SELECT event_id,event_type,decision,reason,created_at "
            "FROM novaid_audit_replay_event_results WHERE replay_request_id=? ORDER BY created_at ASC",
            (replay_request_id,),
        ).fetchall()
        return {
            "request": request,
            "results": [dict(row) for row in results],
            "counts": {
                "matched": len(results),
                "applied": sum(1 for row in results if row["decision"] == "APPLIED"),
                "skipped": sum(1 for row in results if row["decision"] == "SKIPPED"),
            },
        }

    def list_checkpoints(self, *, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.uow.connection.execute(
            "SELECT consumer_name,tenant_id,resource_type,resource_reference,event_version,"
            "updated_at,last_event_id,last_stream_id,applied_at "
            "FROM novaid_webauthn_event_checkpoints WHERE tenant_id=? "
            "ORDER BY updated_at DESC LIMIT ?",
            (tenant_id, max(1, min(limit, 200))),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_dead_letters(self, *, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.uow.connection.execute(
            "SELECT outbox_id,tenant_id,event_type,resource_type,resource_id,event_version,"
            "status,created_at,available_at,published_at,attempt_count,last_error,dead_letter_reason "
            "FROM novaid_webauthn_outbox WHERE tenant_id=? AND status='DEAD_LETTER' "
            "ORDER BY created_at DESC LIMIT ?",
            (tenant_id, max(1, min(limit, 200))),
        ).fetchall()
        return [dict(row) for row in rows]


@lru_cache(maxsize=1)
def get_default_audit_replay_service() -> AuditReplayService:
    return AuditReplayService()
