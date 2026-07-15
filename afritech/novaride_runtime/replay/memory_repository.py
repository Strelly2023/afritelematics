from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass, field

from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository


@dataclass(slots=True)
class MemoryReplayRepository(ReplayPlanRepository):
    plans: dict[tuple[str, str], ReplayPlanRecord] = field(default_factory=dict)
    results: dict[tuple[str, str], ReplayResultRecord] = field(default_factory=dict)
    approvals: dict[tuple[str, str], ReplayApprovalRecord] = field(default_factory=dict)
    transitions: dict[tuple[str, str], list[ReplayTransitionRecord]] = field(default_factory=lambda: defaultdict(list))
    audit: list[RuntimeAuditRecord] = field(default_factory=list)

    async def create(self, plan: ReplayPlanRecord) -> ReplayPlanRecord:
        self.plans[(plan.tenant_id, plan.id)] = deepcopy(plan)
        return deepcopy(plan)

    async def get(self, *, tenant_id: str, plan_id: str) -> ReplayPlanRecord | None:
        plan = self.plans.get((tenant_id, plan_id))
        return deepcopy(plan) if plan is not None else None

    async def list(self, *, tenant_id: str, limit: int = 100, offset: int = 0) -> list[ReplayPlanRecord]:
        values = [deepcopy(plan) for (item_tenant, _), plan in self.plans.items() if item_tenant == tenant_id]
        return values[offset : offset + limit]

    async def update_status(
        self,
        *,
        tenant_id: str,
        plan_id: str,
        expected_version: int,
        new_status: str,
        updated_by: str,
    ) -> ReplayPlanRecord:
        plan = self.plans.get((tenant_id, plan_id))
        if plan is None or plan.version != expected_version:
            raise RuntimeError("replay_plan_version_conflict")
        updated = ReplayPlanRecord(**{**asdict(plan), "status": new_status, "version": plan.version + 1, "updated_by": updated_by})
        self.plans[(tenant_id, plan_id)] = deepcopy(updated)
        return deepcopy(updated)

    async def add_approval(self, approval: ReplayApprovalRecord) -> ReplayApprovalRecord:
        self.approvals[(approval.tenant_id, approval.id)] = deepcopy(approval)
        return deepcopy(approval)

    async def get_approvals(self, *, tenant_id: str, plan_id: str) -> list[ReplayApprovalRecord]:
        return [deepcopy(item) for (item_tenant, _), item in self.approvals.items() if item_tenant == tenant_id and item.replay_plan_id == plan_id]

    async def get_approval(self, *, tenant_id: str, approval_id: str) -> ReplayApprovalRecord | None:
        approval = self.approvals.get((tenant_id, approval_id))
        return deepcopy(approval) if approval is not None else None

    async def consume_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        consumed_by_execution_id: str,
    ) -> ReplayApprovalRecord:
        approval = self.approvals.get((tenant_id, approval_id))
        if approval is None:
            raise RuntimeError("approval_not_found")
        consumed = ReplayApprovalRecord(**{**asdict(approval), "status": "CONSUMED", "consumed_at": approval.created_at, "consumed_by_execution_id": consumed_by_execution_id})
        self.approvals[(tenant_id, approval_id)] = deepcopy(consumed)
        return deepcopy(consumed)

    async def save_result(self, result: ReplayResultRecord) -> ReplayResultRecord:
        self.results[(result.tenant_id, result.replay_plan_id)] = deepcopy(result)
        return deepcopy(result)

    async def get_result(self, *, tenant_id: str, plan_id: str) -> ReplayResultRecord | None:
        result = self.results.get((tenant_id, plan_id))
        return deepcopy(result) if result is not None else None

    async def append_transition(self, transition: ReplayTransitionRecord) -> ReplayTransitionRecord:
        self.transitions[(transition.tenant_id, transition.replay_plan_id)].append(deepcopy(transition))
        return deepcopy(transition)

    async def list_transitions(self, *, tenant_id: str, plan_id: str) -> list[ReplayTransitionRecord]:
        return [deepcopy(item) for item in self.transitions.get((tenant_id, plan_id), [])]

    async def append_audit(self, record: RuntimeAuditRecord) -> RuntimeAuditRecord:
        self.audit.append(deepcopy(record))
        return deepcopy(record)

    async def list_audit(self, *, tenant_id: str, limit: int = 100, offset: int = 0) -> list[RuntimeAuditRecord]:
        values = [deepcopy(item) for item in self.audit if item.tenant_id == tenant_id]
        return values[offset : offset + limit]
