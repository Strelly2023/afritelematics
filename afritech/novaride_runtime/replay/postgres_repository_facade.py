"""Tenant-scoped PostgreSQL replay control-plane repository facade.

The facade is long-lived and stores only PostgresRuntimeSessionFactory.

Every repository operation:
* obtains tenant authority from the operation argument or record;
* opens one short-lived PostgresRuntimeSession;
* lets the session establish transaction-local tenant/RLS authority;
* creates PostgresReplayPlanRepository on that session connection;
* executes one repository operation;
* lets session exit commit or rollback and close deterministically.

No connection, transaction, or tenant state is stored globally.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from afritech.novaride_runtime.persistence.postgres.replay_repository import (
    PostgresReplayPlanRepository,
)
from afritech.novaride_runtime.persistence.postgres.runtime_session import (
    PostgresRuntimeSessionFactory,
)
from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository


T = TypeVar("T")


class TenantScopedPostgresReplayRepository(ReplayPlanRepository):
    """Long-lived facade over short-lived tenant-scoped PostgreSQL sessions."""

    def __init__(
        self,
        session_factory: PostgresRuntimeSessionFactory,
    ) -> None:
        self.session_factory = session_factory

    async def _execute(
        self,
        *,
        tenant_id: str,
        operation: Callable[
            [PostgresReplayPlanRepository],
            Awaitable[T],
        ],
    ) -> T:
        if not tenant_id or not tenant_id.strip():
            raise RuntimeError(
                "replay_repository_tenant_id_required"
            )

        with self.session_factory.session(
            tenant_id=tenant_id,
        ) as session:
            repository = PostgresReplayPlanRepository(
                session.unit_of_work.require_connection()
            )

            return await operation(repository)

    async def create(
        self,
        plan: ReplayPlanRecord,
    ) -> ReplayPlanRecord:
        return await self._execute(
            tenant_id=plan.tenant_id,
            operation=lambda repository: repository.create(plan),
        )

    async def get(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> ReplayPlanRecord | None:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.get(
                tenant_id=tenant_id,
                plan_id=plan_id,
            ),
        )

    async def list(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReplayPlanRecord]:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.list(
                tenant_id=tenant_id,
                limit=limit,
                offset=offset,
            ),
        )

    async def update_status(
        self,
        *,
        tenant_id: str,
        plan_id: str,
        expected_version: int,
        new_status: str,
        updated_by: str,
    ) -> ReplayPlanRecord:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.update_status(
                tenant_id=tenant_id,
                plan_id=plan_id,
                expected_version=expected_version,
                new_status=new_status,
                updated_by=updated_by,
            ),
        )

    async def add_approval(
        self,
        approval: ReplayApprovalRecord,
    ) -> ReplayApprovalRecord:
        return await self._execute(
            tenant_id=approval.tenant_id,
            operation=lambda repository: repository.add_approval(
                approval
            ),
        )

    async def get_approvals(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> list[ReplayApprovalRecord]:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.get_approvals(
                tenant_id=tenant_id,
                plan_id=plan_id,
            ),
        )

    async def get_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
    ) -> ReplayApprovalRecord | None:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.get_approval(
                tenant_id=tenant_id,
                approval_id=approval_id,
            ),
        )

    async def consume_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        consumed_by_execution_id: str,
    ) -> ReplayApprovalRecord:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.consume_approval(
                tenant_id=tenant_id,
                approval_id=approval_id,
                consumed_by_execution_id=consumed_by_execution_id,
            ),
        )

    async def save_result(
        self,
        result: ReplayResultRecord,
    ) -> ReplayResultRecord:
        return await self._execute(
            tenant_id=result.tenant_id,
            operation=lambda repository: repository.save_result(
                result
            ),
        )

    async def get_result(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> ReplayResultRecord | None:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.get_result(
                tenant_id=tenant_id,
                plan_id=plan_id,
            ),
        )

    async def append_transition(
        self,
        transition: ReplayTransitionRecord,
    ) -> ReplayTransitionRecord:
        return await self._execute(
            tenant_id=transition.tenant_id,
            operation=lambda repository: repository.append_transition(
                transition
            ),
        )

    async def list_transitions(
        self,
        *,
        tenant_id: str,
        plan_id: str,
    ) -> list[ReplayTransitionRecord]:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.list_transitions(
                tenant_id=tenant_id,
                plan_id=plan_id,
            ),
        )

    async def append_audit(
        self,
        record: RuntimeAuditRecord,
    ) -> RuntimeAuditRecord:
        return await self._execute(
            tenant_id=record.tenant_id,
            operation=lambda repository: repository.append_audit(
                record
            ),
        )

    async def list_audit(
        self,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuntimeAuditRecord]:
        return await self._execute(
            tenant_id=tenant_id,
            operation=lambda repository: repository.list_audit(
                tenant_id=tenant_id,
                limit=limit,
                offset=offset,
            ),
        )


__all__ = [
    "TenantScopedPostgresReplayRepository",
]
