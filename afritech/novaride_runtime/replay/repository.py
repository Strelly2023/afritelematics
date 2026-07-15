from __future__ import annotations

from typing import Protocol

from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)


class ReplayPlanRepository(Protocol):
    async def create(self, plan: ReplayPlanRecord) -> ReplayPlanRecord: ...

    async def get(self, *, tenant_id: str, plan_id: str) -> ReplayPlanRecord | None: ...

    async def list(self, *, tenant_id: str, limit: int = 100, offset: int = 0) -> list[ReplayPlanRecord]: ...

    async def update_status(
        self,
        *,
        tenant_id: str,
        plan_id: str,
        expected_version: int,
        new_status: str,
        updated_by: str,
    ) -> ReplayPlanRecord: ...

    async def add_approval(self, approval: ReplayApprovalRecord) -> ReplayApprovalRecord: ...

    async def get_approvals(self, *, tenant_id: str, plan_id: str) -> list[ReplayApprovalRecord]: ...

    async def get_approval(self, *, tenant_id: str, approval_id: str) -> ReplayApprovalRecord | None: ...

    async def consume_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        consumed_by_execution_id: str,
    ) -> ReplayApprovalRecord: ...

    async def save_result(self, result: ReplayResultRecord) -> ReplayResultRecord: ...

    async def get_result(self, *, tenant_id: str, plan_id: str) -> ReplayResultRecord | None: ...

    async def append_transition(self, transition: ReplayTransitionRecord) -> ReplayTransitionRecord: ...

    async def list_transitions(self, *, tenant_id: str, plan_id: str) -> list[ReplayTransitionRecord]: ...

    async def append_audit(self, record: RuntimeAuditRecord) -> RuntimeAuditRecord: ...

    async def list_audit(self, *, tenant_id: str, limit: int = 100, offset: int = 0) -> list[RuntimeAuditRecord]: ...
