from __future__ import annotations

from dataclasses import asdict
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.events.replay import canonical_state_hash, rebuild_projection
from afritech.novaride_runtime.events.replay_verifier import verify_replay
from afritech.novaride_runtime.replay.hashing import replay_plan_hash
from afritech.novaride_runtime.replay.lifecycle import ensure_replay_transition
from afritech.novaride_runtime.replay.models import (
    ReplayApprovalRecord,
    ReplayPlanRecord,
    ReplayResultRecord,
    ReplayTransitionRecord,
    RuntimeAuditRecord,
)
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository
from afritech.novaride_runtime.security import NovaRideRuntimeContext, normalize_role


class InvalidReplayTransition(RuntimeError):
    pass


class ReplayService:
    def __init__(self, repository: ReplayPlanRepository) -> None:
        self.repository = repository

    async def create_plan(
        self,
        *,
        payload: Any,
        actor: NovaRideRuntimeContext,
        idempotency_key: str,
    ) -> ReplayPlanRecord:
        plan_id = new_id("replay")
        plan = ReplayPlanRecord(
            id=plan_id,
            tenant_id=actor.tenant_id,
            organization_id=actor.organization_id,
            workspace_id=actor.workspace_id,
            name=getattr(payload, "name", "NovaRide replay plan"),
            description=getattr(payload, "description", None),
            scenario_type=getattr(payload, "scenario_type", payload.mode.value if hasattr(payload, "mode") else "runtime"),
            source_reference=getattr(payload, "source_reference", None),
            target_environment=getattr(payload, "target_environment", "production"),
            status="READY_FOR_EXECUTION",
            risk_level=getattr(payload, "risk_level", "medium"),
            actions=tuple(getattr(payload, "actions", []) or []),
            affected_resources=tuple(getattr(payload, "affected_resources", []) or []),
            validation_requirements=tuple(getattr(payload, "validation_requirements", []) or []),
            rollback_plan=getattr(payload, "rollback_plan", {}) or {},
            version=1,
            idempotency_key=idempotency_key,
            created_by=actor.subject_id,
            created_at=utc_now().isoformat(),
            updated_by=actor.subject_id,
            updated_at=utc_now().isoformat(),
        )
        plan = ReplayPlanRecord(**{**asdict(plan), "plan_hash": replay_plan_hash(plan)})
        return await self.repository.create(plan)

    async def get_plan(self, *, tenant_id: str, plan_id: str) -> ReplayPlanRecord | None:
        return await self.repository.get(tenant_id=tenant_id, plan_id=plan_id)

    async def list_plans(self, *, tenant_id: str, limit: int = 100, offset: int = 0) -> list[ReplayPlanRecord]:
        return await self.repository.list(tenant_id=tenant_id, limit=limit, offset=offset)

    async def execute_plan(self, *, plan: ReplayPlanRecord, actor: NovaRideRuntimeContext, validate_only: bool = False) -> ReplayResultRecord:
        if not validate_only:
            ensure_replay_transition(plan.status, "EXECUTING")
        events: list[Any] = []
        verification = verify_replay(replay_id=plan.id, events=events)
        result_payload = verification.as_dict()
        result_payload["state"] = "MATCHED" if verification.matched else "DIVERGED"
        result_payload["validate_only"] = validate_only
        result = ReplayResultRecord(
            id=new_id("replay_result"),
            tenant_id=plan.tenant_id,
            replay_plan_id=plan.id,
            plan_version=plan.version,
            execution_status="EXECUTED",
            validation_status="VALIDATION_REQUIRED" if not validate_only else "VALIDATED",
            result_payload=result_payload,
            result_hash=canonical_state_hash(result_payload),
            executed_by=actor.subject_id,
            validated_by=actor.subject_id if validate_only else None,
            executed_at=utc_now().isoformat(),
            validated_at=utc_now().isoformat() if validate_only else None,
        )
        await self.repository.save_result(result)
        new_status = "EXECUTED" if not validate_only else plan.status
        if not validate_only:
            await self.repository.update_status(
                tenant_id=plan.tenant_id,
                plan_id=plan.id,
                expected_version=plan.version,
                new_status=new_status,
                updated_by=actor.subject_id,
            )
            await self.repository.append_transition(
                ReplayTransitionRecord(
                    id=new_id("transition"),
                    tenant_id=plan.tenant_id,
                    replay_plan_id=plan.id,
                    from_status=plan.status,
                    to_status=new_status,
                    version=plan.version + 1,
                    actor_id=actor.subject_id,
                    reason="execution",
                    occurred_at=utc_now().isoformat(),
                )
            )
        return result

    async def validate_plan(self, *, plan: ReplayPlanRecord, result: ReplayResultRecord, actor: NovaRideRuntimeContext) -> ReplayResultRecord:
        if result.executed_by == actor.subject_id:
            raise InvalidReplayTransition("executor_cannot_validate_own_result")
        updated = ReplayResultRecord(
            **{**asdict(result), "validation_status": "VALIDATED", "validated_by": actor.subject_id, "validated_at": utc_now().isoformat()}
        )
        await self.repository.save_result(updated)
        await self.repository.update_status(
            tenant_id=plan.tenant_id,
            plan_id=plan.id,
            expected_version=plan.version,
            new_status="VALIDATED",
            updated_by=actor.subject_id,
        )
        return updated

    async def record_approval_vote(
        self,
        *,
        plan: ReplayPlanRecord,
        actor: NovaRideRuntimeContext,
        decision: str,
        reason: str | None = None,
    ) -> ReplayApprovalRecord:
        if actor.subject_id == plan.created_by:
            raise InvalidReplayTransition("replay_creator_cannot_approve_own_plan")
        if decision not in {"APPROVE", "REJECT", "REQUEST_CHANGES", "ABSTAIN"}:
            raise InvalidReplayTransition("invalid_approval_decision")
        if decision != "APPROVE":
            raise InvalidReplayTransition("approval_vote_not_accepted")
        current_votes = await self.repository.get_approvals(tenant_id=plan.tenant_id, plan_id=plan.id)
        if any(v.approver_id == actor.subject_id for v in current_votes):
            raise InvalidReplayTransition("duplicate_approval_vote")
        vote = ReplayApprovalRecord(
            id=new_id("approval"),
            tenant_id=plan.tenant_id,
            replay_plan_id=plan.id,
            plan_version=plan.version,
            plan_hash=plan.plan_hash,
            required_quorum=2,
            status="APPROVED",
            approver_id=actor.subject_id,
            approver_role=next(iter(actor.roles), "UNKNOWN"),
            decision=decision,
            reason=reason,
            created_at=utc_now().isoformat(),
        )
        await self.repository.add_approval(vote)
        return vote

    async def promote_plan(
        self,
        *,
        plan: ReplayPlanRecord,
        actor: NovaRideRuntimeContext,
    ) -> ReplayPlanRecord:
        approvals = await self.repository.get_approvals(tenant_id=plan.tenant_id, plan_id=plan.id)
        if actor.subject_id == plan.created_by:
            raise InvalidReplayTransition("replay_creator_cannot_approve_own_plan")
        if actor.subject_id in {approval.approver_id for approval in approvals}:
            raise InvalidReplayTransition("replay_approver_cannot_execute_promotion")
        if plan.status not in {"APPROVAL_REQUIRED", "APPROVED", "VALIDATED", "EXECUTED"}:
            raise InvalidReplayTransition(f"invalid_replay_transition:{plan.status}->PROMOTING")
        result = await self.repository.get_result(tenant_id=plan.tenant_id, plan_id=plan.id)
        if result is None or result.validation_status not in {"VALIDATED", "VALIDATION_REQUIRED"}:
            raise InvalidReplayTransition("promotion_requires_validated_result")
        votes = [approval for approval in approvals if approval.plan_version == plan.version and approval.plan_hash == plan.plan_hash and approval.status == "APPROVED"]
        roles = {approval.approver_role for approval in votes}
        if len(votes) < 2:
            raise InvalidReplayTransition("approval_quorum_required")
        if not (roles.intersection({"OPERATIONS_TEAM", "PROJECT_MANAGER"}) and roles.intersection({"QA_ENGINEER", "SECURITY_ENGINEER"})):
            raise InvalidReplayTransition("approval_role_quorum_required")
        consumed = await self.repository.consume_approval(
            tenant_id=plan.tenant_id,
            approval_id=votes[0].id,
            consumed_by_execution_id=result.id,
        )
        if consumed.status != "CONSUMED":
            raise InvalidReplayTransition("approval_consumption_failed")
        promoted = await self.repository.update_status(
            tenant_id=plan.tenant_id,
            plan_id=plan.id,
            expected_version=plan.version,
            new_status="PROMOTED",
            updated_by=actor.subject_id,
        )
        return promoted

    async def audit(
        self,
        *,
        actor: NovaRideRuntimeContext,
        action: str,
        subject_type: str,
        subject_id: str,
        result: str,
        correlation_id: str,
        payload_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeAuditRecord:
        record = RuntimeAuditRecord(
            id=new_id("audit"),
            tenant_id=actor.tenant_id,
            actor_id=actor.subject_id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            result=result,
            correlation_id=correlation_id,
            payload_hash=payload_hash,
            metadata=metadata or {},
            occurred_at=utc_now().isoformat(),
        )
        return await self.repository.append_audit(record)
