"""PostgreSQL authority adapter for the NovaRide replay control plane.

The adapter owns no connection lifecycle and no transaction boundary.
It operates on the transaction-scoped connection supplied by the
PostgreSQL runtime session.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from psycopg.types.json import Jsonb

from afritech.novaride_runtime.persistence.postgres.connection import (
    PostgresConnectionProtocol,
)
from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository


def _row_mapping(cursor: Any, row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)

    description = cursor.description
    if description is None:
        raise RuntimeError("replay_query_missing_cursor_description")

    return {
        column.name: value
        for column, value in zip(description, row, strict=True)
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _plan(row: Mapping[str, Any]) -> ReplayPlanRecord:
    return ReplayPlanRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        organization_id=str(row["organization_id"]),
        workspace_id=_optional_text(row.get("workspace_id")),
        name=str(row["name"]),
        description=_optional_text(row.get("description")),
        scenario_type=str(row["scenario_type"]),
        source_reference=_optional_text(row.get("source_reference")),
        target_environment=str(row["target_environment"]),
        status=str(row["status"]),
        risk_level=str(row["risk_level"]),
        actions=tuple(row.get("actions") or []),
        affected_resources=tuple(row.get("affected_resources") or []),
        validation_requirements=tuple(
            row.get("validation_requirements") or []
        ),
        rollback_plan=dict(row.get("rollback_plan") or {}),
        plan_hash=str(row["plan_hash"]),
        version=int(row["version"]),
        idempotency_key=str(row["idempotency_key"]),
        created_by=str(row["created_by"]),
        created_at=_text(row.get("created_at")),
        updated_by=str(row["updated_by"]),
        updated_at=_text(row.get("updated_at")),
        approved_at=_optional_text(row.get("approved_at")),
        promoted_at=_optional_text(row.get("promoted_at")),
    )


def _approval(row: Mapping[str, Any]) -> ReplayApprovalRecord:
    return ReplayApprovalRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        replay_plan_id=str(row["replay_plan_id"]),
        plan_version=int(row["plan_version"]),
        plan_hash=str(row["plan_hash"]),
        required_quorum=int(row["required_quorum"]),
        status=str(row["status"]),
        approver_id=_text(row.get("approver_id")),
        approver_role=_text(row.get("approver_role")),
        decision=_text(row.get("decision")) or "APPROVE",
        reason=_optional_text(row.get("reason")),
        expires_at=_optional_text(row.get("expires_at")),
        consumed_at=_optional_text(row.get("consumed_at")),
        consumed_by_execution_id=_optional_text(
            row.get("consumed_by_execution_id")
        ),
        created_at=_text(row.get("created_at")),
    )


def _result(row: Mapping[str, Any]) -> ReplayResultRecord:
    return ReplayResultRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        replay_plan_id=str(row["replay_plan_id"]),
        plan_version=int(row["plan_version"]),
        execution_status=str(row["execution_status"]),
        validation_status=str(row["validation_status"]),
        result_payload=dict(row.get("result_payload") or {}),
        result_hash=str(row["result_hash"]),
        executed_by=str(row["executed_by"]),
        validated_by=_optional_text(row.get("validated_by")),
        executed_at=_text(row.get("executed_at")),
        validated_at=_optional_text(row.get("validated_at")),
    )


def _transition(row: Mapping[str, Any]) -> ReplayTransitionRecord:
    return ReplayTransitionRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        replay_plan_id=str(row["replay_plan_id"]),
        from_status=str(row["from_status"]),
        to_status=str(row["to_status"]),
        version=int(row["version"]),
        actor_id=str(row["actor_id"]),
        reason=_optional_text(row.get("reason")),
        occurred_at=_text(row.get("occurred_at")),
    )


def _audit(row: Mapping[str, Any]) -> RuntimeAuditRecord:
    return RuntimeAuditRecord(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        actor_id=str(row["actor_id"]),
        action=str(row["action"]),
        subject_type=str(row["subject_type"]),
        subject_id=str(row["subject_id"]),
        result=str(row["result"]),
        correlation_id=str(row["correlation_id"]),
        payload_hash=_optional_text(row.get("payload_hash")),
        metadata=dict(row.get("metadata") or {}),
        occurred_at=_text(row.get("occurred_at")),
    )


class PostgresReplayPlanRepository(ReplayPlanRepository):
    """Replay control-plane repository on an existing PostgreSQL transaction."""

    def __init__(
        self,
        connection: PostgresConnectionProtocol,
    ) -> None:
        self.connection = connection

    async def create(
        self,
        plan: ReplayPlanRecord,
    ) -> ReplayPlanRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_replay_plans (
                id, tenant_id, organization_id, workspace_id,
                name, description, scenario_type, source_reference,
                target_environment, status, risk_level,
                actions, affected_resources, validation_requirements,
                rollback_plan, plan_hash, version, idempotency_key,
                created_by, created_at, updated_by, updated_at,
                approved_at, promoted_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            """,
            (
                plan.id,
                plan.tenant_id,
                plan.organization_id,
                plan.workspace_id,
                plan.name,
                plan.description,
                plan.scenario_type,
                plan.source_reference,
                plan.target_environment,
                plan.status,
                plan.risk_level,
                Jsonb(list(plan.actions)),
                Jsonb(list(plan.affected_resources)),
                Jsonb(list(plan.validation_requirements)),
                Jsonb(plan.rollback_plan),
                plan.plan_hash,
                plan.version,
                plan.idempotency_key,
                plan.created_by,
                plan.created_at,
                plan.updated_by,
                plan.updated_at,
                plan.approved_at,
                plan.promoted_at,
            ),
        )
        return plan

    async def get(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> ReplayPlanRecord | None:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_replay_plans
            WHERE tenant_id = %s
              AND id = %s
            """,
            (tenant_id, plan_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _plan(_row_mapping(cursor, row))

    async def list(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReplayPlanRecord]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_replay_plans
            WHERE tenant_id = %s
            ORDER BY created_at DESC, id
            LIMIT %s OFFSET %s
            """,
            (tenant_id, limit, offset),
        )
        return [
            _plan(_row_mapping(cursor, row))
            for row in cursor.fetchall()
        ]

    async def update_status(
        self,
        *,
        tenant_id: str,
        plan_id: str,
        expected_version: int,
        new_status: str,
        updated_by: str,
    ) -> ReplayPlanRecord:
        cursor = self.connection.execute(
            """
            UPDATE novaride_replay_plans
            SET status = %s,
                version = version + 1,
                updated_by = %s,
                updated_at = now()
            WHERE tenant_id = %s
              AND id = %s
              AND version = %s
            RETURNING *
            """,
            (
                new_status,
                updated_by,
                tenant_id,
                plan_id,
                expected_version,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("replay_plan_version_conflict")
        return _plan(_row_mapping(cursor, row))

    async def add_approval(
        self,
        approval: ReplayApprovalRecord,
    ) -> ReplayApprovalRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_replay_approvals (
                id, tenant_id, replay_plan_id, plan_version,
                plan_hash, required_quorum, status, expires_at,
                consumed_at, consumed_by_execution_id, created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (
                approval.id,
                approval.tenant_id,
                approval.replay_plan_id,
                approval.plan_version,
                approval.plan_hash,
                approval.required_quorum,
                approval.status,
                approval.expires_at,
                approval.consumed_at,
                approval.consumed_by_execution_id,
                approval.created_at,
            ),
        )

        if approval.approver_id:
            self.connection.execute(
                """
                INSERT INTO novaride_replay_approval_votes (
                    id, tenant_id, approval_id, approver_id,
                    approver_role, decision, reason, decided_at
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (
                    tenant_id,
                    approval_id,
                    approver_id
                ) DO NOTHING
                """,
                (
                    approval.id,
                    approval.tenant_id,
                    approval.id,
                    approval.approver_id,
                    approval.approver_role,
                    approval.decision,
                    approval.reason,
                    approval.created_at,
                ),
            )

        return approval

    async def get_approvals(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> list[ReplayApprovalRecord]:
        cursor = self.connection.execute(
            """
            SELECT
                a.*,
                v.approver_id,
                v.approver_role,
                v.decision,
                v.reason
            FROM novaride_replay_approvals AS a
            LEFT JOIN LATERAL (
                SELECT
                    approver_id,
                    approver_role,
                    decision,
                    reason
                FROM novaride_replay_approval_votes
                WHERE tenant_id = a.tenant_id
                  AND approval_id = a.id
                ORDER BY decided_at DESC, id DESC
                LIMIT 1
            ) AS v ON TRUE
            WHERE a.tenant_id = %s
              AND a.replay_plan_id = %s
            ORDER BY a.created_at ASC, a.id
            """,
            (tenant_id, plan_id),
        )
        return [
            _approval(_row_mapping(cursor, row))
            for row in cursor.fetchall()
        ]

    async def get_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
    ) -> ReplayApprovalRecord | None:
        cursor = self.connection.execute(
            """
            SELECT
                a.*,
                v.approver_id,
                v.approver_role,
                v.decision,
                v.reason
            FROM novaride_replay_approvals AS a
            LEFT JOIN LATERAL (
                SELECT
                    approver_id,
                    approver_role,
                    decision,
                    reason
                FROM novaride_replay_approval_votes
                WHERE tenant_id = a.tenant_id
                  AND approval_id = a.id
                ORDER BY decided_at DESC, id DESC
                LIMIT 1
            ) AS v ON TRUE
            WHERE a.tenant_id = %s
              AND a.id = %s
            """,
            (tenant_id, approval_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _approval(_row_mapping(cursor, row))

    async def consume_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        consumed_by_execution_id: str,
    ) -> ReplayApprovalRecord:
        cursor = self.connection.execute(
            """
            UPDATE novaride_replay_approvals
            SET consumed_at = now(),
                consumed_by_execution_id = %s
            WHERE tenant_id = %s
              AND id = %s
              AND consumed_at IS NULL
            RETURNING *
            """,
            (
                consumed_by_execution_id,
                tenant_id,
                approval_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("replay_approval_not_consumable")

        mapped = _row_mapping(cursor, row)
        mapped.setdefault("approver_id", "")
        mapped.setdefault("approver_role", "")
        mapped.setdefault("decision", "APPROVE")
        mapped.setdefault("reason", None)
        return _approval(mapped)

    async def save_result(
        self,
        result: ReplayResultRecord,
    ) -> ReplayResultRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_replay_results (
                id, tenant_id, replay_plan_id, plan_version,
                execution_status, validation_status,
                result_payload, result_hash,
                executed_by, validated_by,
                executed_at, validated_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                result.id,
                result.tenant_id,
                result.replay_plan_id,
                result.plan_version,
                result.execution_status,
                result.validation_status,
                Jsonb(result.result_payload),
                result.result_hash,
                result.executed_by,
                result.validated_by,
                result.executed_at,
                result.validated_at,
            ),
        )
        return result

    async def get_result(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> ReplayResultRecord | None:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_replay_results
            WHERE tenant_id = %s
              AND replay_plan_id = %s
            ORDER BY executed_at DESC, id DESC
            LIMIT 1
            """,
            (tenant_id, plan_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _result(_row_mapping(cursor, row))

    async def append_transition(
        self,
        transition: ReplayTransitionRecord,
    ) -> ReplayTransitionRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_replay_transitions (
                id, tenant_id, replay_plan_id,
                from_status, to_status, version,
                actor_id, reason, occurred_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> list[ReplayTransitionRecord]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_replay_transitions
            WHERE tenant_id = %s
              AND replay_plan_id = %s
            ORDER BY occurred_at ASC, id ASC
            """,
            (tenant_id, plan_id),
        )
        return [
            _transition(_row_mapping(cursor, row))
            for row in cursor.fetchall()
        ]

    async def append_audit(
        self,
        record: RuntimeAuditRecord,
    ) -> RuntimeAuditRecord:
        self.connection.execute(
            """
            INSERT INTO novaride_runtime_audit (
                id, tenant_id, actor_id, action,
                subject_type, subject_id, result,
                correlation_id, payload_hash,
                metadata, occurred_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
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
                Jsonb(record.metadata),
                record.occurred_at,
            ),
        )
        return record

    async def list_audit(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuntimeAuditRecord]:
        cursor = self.connection.execute(
            """
            SELECT *
            FROM novaride_runtime_audit
            WHERE tenant_id = %s
            ORDER BY occurred_at DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            (tenant_id, limit, offset),
        )
        return [
            _audit(_row_mapping(cursor, row))
            for row in cursor.fetchall()
        ]


__all__ = [
    "PostgresReplayPlanRepository",
]
