from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from threading import Lock
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _loads(value: str | bytes | None) -> Any:
    if value in (None, ""):
        return None
    return json.loads(value)


class PostgresReplayRepository(ReplayPlanRepository):
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS novaride_replay_plans (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    workspace_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    scenario_type TEXT NOT NULL,
                    source_reference TEXT,
                    target_environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    actions TEXT NOT NULL DEFAULT '[]',
                    affected_resources TEXT NOT NULL DEFAULT '[]',
                    validation_requirements TEXT NOT NULL DEFAULT '[]',
                    rollback_plan TEXT NOT NULL DEFAULT '{}',
                    plan_hash TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    idempotency_key TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    approved_at TEXT,
                    promoted_at TEXT,
                    UNIQUE (tenant_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS novaride_replay_results (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    replay_plan_id TEXT NOT NULL,
                    plan_version INTEGER NOT NULL,
                    execution_status TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    result_payload TEXT NOT NULL,
                    result_hash TEXT NOT NULL,
                    executed_by TEXT NOT NULL,
                    validated_by TEXT,
                    executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    validated_at TEXT,
                    FOREIGN KEY (replay_plan_id) REFERENCES novaride_replay_plans(id)
                );
                CREATE TABLE IF NOT EXISTS novaride_replay_approvals (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    replay_plan_id TEXT NOT NULL,
                    plan_version INTEGER NOT NULL,
                    plan_hash TEXT NOT NULL,
                    required_quorum INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    approver_id TEXT NOT NULL DEFAULT '',
                    approver_role TEXT NOT NULL DEFAULT '',
                    decision TEXT NOT NULL DEFAULT 'APPROVE',
                    reason TEXT,
                    expires_at TEXT,
                    consumed_at TEXT,
                    consumed_by_execution_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (replay_plan_id) REFERENCES novaride_replay_plans(id)
                    ,
                    UNIQUE (tenant_id, replay_plan_id, approver_id)
                );
                CREATE TABLE IF NOT EXISTS novaride_replay_approval_votes (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    approval_id TEXT NOT NULL,
                    approver_id TEXT NOT NULL,
                    approver_role TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (approval_id) REFERENCES novaride_replay_approvals(id),
                    UNIQUE (tenant_id, approval_id, approver_id)
                );
                CREATE TABLE IF NOT EXISTS novaride_replay_transitions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    replay_plan_id TEXT NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    actor_id TEXT NOT NULL,
                    reason TEXT,
                    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS novaride_runtime_audit (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    subject_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    payload_hash TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS novaride_runtime_idempotency (
                    tenant_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    response_status INTEGER NOT NULL,
                    response_body TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    PRIMARY KEY (tenant_id, operation, idempotency_key)
                );
                """
            )

    async def create(self, plan: ReplayPlanRecord) -> ReplayPlanRecord:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novaride_replay_plans (
                    id, tenant_id, organization_id, workspace_id, name, description,
                    scenario_type, source_reference, target_environment, status,
                    risk_level, actions, affected_resources, validation_requirements,
                    rollback_plan, plan_hash, version, idempotency_key, created_by,
                    created_at, updated_by, updated_at, approved_at, promoted_at
                ) VALUES (
                    :id, :tenant_id, :organization_id, :workspace_id, :name, :description,
                    :scenario_type, :source_reference, :target_environment, :status,
                    :risk_level, :actions, :affected_resources, :validation_requirements,
                    :rollback_plan, :plan_hash, :version, :idempotency_key, :created_by,
                    :created_at, :updated_by, :updated_at, :approved_at, :promoted_at
                )
                """,
                {
                    **asdict(plan),
                    "actions": _json(list(plan.actions)),
                    "affected_resources": _json(list(plan.affected_resources)),
                    "validation_requirements": _json(list(plan.validation_requirements)),
                    "rollback_plan": _json(plan.rollback_plan),
                },
            )
        return plan

    async def get(self, *, tenant_id: str, plan_id: str) -> ReplayPlanRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM novaride_replay_plans WHERE tenant_id = ? AND id = ?",
                (tenant_id, plan_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_plan(row)

    async def list(
        self, *, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[ReplayPlanRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM novaride_replay_plans WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (tenant_id, limit, offset),
            ).fetchall()
        return [self._row_to_plan(row) for row in rows]

    async def update_status(
        self,
        *,
        tenant_id: str,
        plan_id: str,
        expected_version: int,
        new_status: str,
        updated_by: str,
    ) -> ReplayPlanRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM novaride_replay_plans
                WHERE tenant_id = ? AND id = ? AND version = ?
                """,
                (tenant_id, plan_id, expected_version),
            ).fetchone()
            if row is None:
                raise RuntimeError("replay_plan_version_conflict")
            current = self._row_to_plan(row)
            updated = ReplayPlanRecord(
                **{
                    **asdict(current),
                    "status": new_status,
                    "version": current.version + 1,
                    "updated_by": updated_by,
                    "updated_at": utc_now().isoformat(),
                }
            )
            conn.execute(
                """
                UPDATE novaride_replay_plans
                SET status = ?, version = ?, updated_by = ?, updated_at = ?
                WHERE tenant_id = ? AND id = ? AND version = ?
                """,
                (
                    updated.status,
                    updated.version,
                    updated.updated_by,
                    updated.updated_at,
                    tenant_id,
                    plan_id,
                    expected_version,
                ),
            )
        return updated

    async def add_approval(self, approval: ReplayApprovalRecord) -> ReplayApprovalRecord:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novaride_replay_approvals (
                    id, tenant_id, replay_plan_id, plan_version, plan_hash,
                    required_quorum, status, approver_id, approver_role, decision, reason,
                    expires_at, consumed_at,
                    consumed_by_execution_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval.id,
                    approval.tenant_id,
                    approval.replay_plan_id,
                    approval.plan_version,
                    approval.plan_hash,
                    approval.required_quorum,
                    approval.status,
                    approval.approver_id,
                    approval.approver_role,
                    approval.decision,
                    approval.reason,
                    approval.expires_at,
                    approval.consumed_at,
                    approval.consumed_by_execution_id,
                    approval.created_at,
                ),
            )
        return approval

    async def get_approvals(self, *, tenant_id: str, plan_id: str) -> list[ReplayApprovalRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM novaride_replay_approvals WHERE tenant_id = ? AND replay_plan_id = ? ORDER BY created_at ASC",
                (tenant_id, plan_id),
            ).fetchall()
        return [self._row_to_approval(row) for row in rows]

    async def get_approval(
        self, *, tenant_id: str, approval_id: str
    ) -> ReplayApprovalRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM novaride_replay_approvals WHERE tenant_id = ? AND id = ?",
                (tenant_id, approval_id),
            ).fetchone()
        return self._row_to_approval(row) if row is not None else None

    async def consume_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        consumed_by_execution_id: str,
    ) -> ReplayApprovalRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM novaride_replay_approvals WHERE tenant_id = ? AND id = ?",
                (tenant_id, approval_id),
            ).fetchone()
            if row is None:
                raise RuntimeError("approval_not_found")
            approval = self._row_to_approval(row)
            consumed = ReplayApprovalRecord(
                **{
                    **asdict(approval),
                    "status": "CONSUMED",
                    "consumed_at": utc_now().isoformat(),
                    "consumed_by_execution_id": consumed_by_execution_id,
                }
            )
            conn.execute(
                """
                UPDATE novaride_replay_approvals
                SET status = ?, consumed_at = ?, consumed_by_execution_id = ?
                WHERE tenant_id = ? AND id = ?
                """,
                (
                    consumed.status,
                    consumed.consumed_at,
                    consumed.consumed_by_execution_id,
                    tenant_id,
                    approval_id,
                ),
            )
        return consumed

    async def save_result(self, result: ReplayResultRecord) -> ReplayResultRecord:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO novaride_replay_results (
                    id, tenant_id, replay_plan_id, plan_version, execution_status,
                    validation_status, result_payload, result_hash, executed_by,
                    validated_by, executed_at, validated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.tenant_id,
                    result.replay_plan_id,
                    result.plan_version,
                    result.execution_status,
                    result.validation_status,
                    _json(result.result_payload),
                    result.result_hash,
                    result.executed_by,
                    result.validated_by,
                    result.executed_at,
                    result.validated_at,
                ),
            )
        return result

    async def get_result(self, *, tenant_id: str, plan_id: str) -> ReplayResultRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM novaride_replay_results WHERE tenant_id = ? AND replay_plan_id = ? ORDER BY executed_at DESC LIMIT 1",
                (tenant_id, plan_id),
            ).fetchone()
        return self._row_to_result(row) if row is not None else None

    async def append_transition(self, transition: ReplayTransitionRecord) -> ReplayTransitionRecord:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novaride_replay_transitions (
                    id, tenant_id, replay_plan_id, from_status, to_status, version,
                    actor_id, reason, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition.id,
                    transition.tenant_id,
                    transition.replay_plan_id,
                    transition.from_status,
                    transition.to_status,
                    transition.version,
                    transition.actor_id,
                    transition.reason,
                    transition.occurred_at,
                ),
            )
        return transition

    async def list_transitions(
        self, *, tenant_id: str, plan_id: str
    ) -> list[ReplayTransitionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM novaride_replay_transitions WHERE tenant_id = ? AND replay_plan_id = ? ORDER BY occurred_at ASC",
                (tenant_id, plan_id),
            ).fetchall()
        return [self._row_to_transition(row) for row in rows]

    async def append_audit(self, record: RuntimeAuditRecord) -> RuntimeAuditRecord:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novaride_runtime_audit (
                    id, tenant_id, actor_id, action, subject_type, subject_id,
                    result, correlation_id, payload_hash, metadata, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.tenant_id,
                    record.actor_id,
                    record.action,
                    record.subject_type,
                    record.subject_id,
                    record.result,
                    record.correlation_id,
                    record.payload_hash,
                    _json(record.metadata),
                    record.occurred_at,
                ),
            )
        return record

    async def list_audit(
        self, *, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[RuntimeAuditRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM novaride_runtime_audit WHERE tenant_id = ? ORDER BY occurred_at DESC LIMIT ? OFFSET ?",
                (tenant_id, limit, offset),
            ).fetchall()
        return [self._row_to_audit(row) for row in rows]

    def _row_to_plan(self, row: sqlite3.Row) -> ReplayPlanRecord:
        return ReplayPlanRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            organization_id=row["organization_id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            description=row["description"],
            scenario_type=row["scenario_type"],
            source_reference=row["source_reference"],
            target_environment=row["target_environment"],
            status=row["status"],
            risk_level=row["risk_level"],
            actions=tuple(_loads(row["actions"]) or []),
            affected_resources=tuple(_loads(row["affected_resources"]) or []),
            validation_requirements=tuple(_loads(row["validation_requirements"]) or []),
            rollback_plan=_loads(row["rollback_plan"]) or {},
            plan_hash=row["plan_hash"],
            version=int(row["version"]),
            idempotency_key=row["idempotency_key"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_by=row["updated_by"],
            updated_at=row["updated_at"],
            approved_at=row["approved_at"],
            promoted_at=row["promoted_at"],
        )

    def _row_to_approval(self, row: sqlite3.Row) -> ReplayApprovalRecord:
        return ReplayApprovalRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            replay_plan_id=row["replay_plan_id"],
            plan_version=int(row["plan_version"]),
            plan_hash=row["plan_hash"],
            required_quorum=int(row["required_quorum"]),
            status=row["status"],
            approver_id=row["approver_id"],
            approver_role=row["approver_role"],
            decision=row["decision"],
            reason=row["reason"],
            expires_at=row["expires_at"],
            consumed_at=row["consumed_at"],
            consumed_by_execution_id=row["consumed_by_execution_id"],
            created_at=row["created_at"],
        )

    def _row_to_result(self, row: sqlite3.Row) -> ReplayResultRecord:
        return ReplayResultRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            replay_plan_id=row["replay_plan_id"],
            plan_version=int(row["plan_version"]),
            execution_status=row["execution_status"],
            validation_status=row["validation_status"],
            result_payload=_loads(row["result_payload"]) or {},
            result_hash=row["result_hash"],
            executed_by=row["executed_by"],
            validated_by=row["validated_by"],
            executed_at=row["executed_at"],
            validated_at=row["validated_at"],
        )

    def _row_to_transition(self, row: sqlite3.Row) -> ReplayTransitionRecord:
        return ReplayTransitionRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            replay_plan_id=row["replay_plan_id"],
            from_status=row["from_status"],
            to_status=row["to_status"],
            version=int(row["version"]),
            actor_id=row["actor_id"],
            reason=row["reason"],
            occurred_at=row["occurred_at"],
        )

    def _row_to_audit(self, row: sqlite3.Row) -> RuntimeAuditRecord:
        return RuntimeAuditRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            actor_id=row["actor_id"],
            action=row["action"],
            subject_type=row["subject_type"],
            subject_id=row["subject_id"],
            result=row["result"],
            correlation_id=row["correlation_id"],
            payload_hash=row["payload_hash"],
            metadata=_loads(row["metadata"]) or {},
            occurred_at=row["occurred_at"],
        )


SQLiteReplayRepository = PostgresReplayRepository
