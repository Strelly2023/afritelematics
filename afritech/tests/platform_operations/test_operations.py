from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.data_governance.lifecycle import (
    DataClassification,
    DataLifecyclePolicy,
    RetentionClass,
    evaluate_deletion,
    validate_residency,
)
from afritech.platform_operations.feature_flags import FeatureFlag, flag_enabled
from afritech.platform_operations.policy import PolicyInput, VersionedPolicyEngine
from afritech.platform_operations.reliability import (
    ServiceObjective,
    evaluate_error_budget,
)
from afritech.platform_operations.rollout import RolloutPlan, evaluate_rollout
from afritech.platform_operations.workflow import (
    DurableWorkflowEngine,
    InMemoryWorkflowStore,
    SQLiteWorkflowStore,
    WorkflowDefinition,
    WorkflowStep,
)


def test_versioned_policy_engine_is_fail_closed_and_traceable() -> None:
    engine = VersionedPolicyEngine()
    allowed = engine.evaluate(
        PolicyInput(
            tenant_id="tenant-a",
            identity_tenant_id="tenant-a",
            actor_id="actor-a",
            roles=("OPERATOR",),
            scopes=("payments:write",),
            action="payment.execute",
            required_roles=("OPERATOR",),
            required_scopes=("payments:write",),
            resource_owner_id="actor-a",
            risk_score=Decimal("0.10"),
        )
    )
    denied = engine.evaluate(
        PolicyInput(
            tenant_id="tenant-b",
            identity_tenant_id="tenant-a",
            actor_id="actor-a",
            roles=("OBSERVER",),
            scopes=(),
            action="payment.execute",
            required_roles=("OPERATOR",),
            required_scopes=("payments:write",),
            resource_owner_id="actor-b",
            risk_score=Decimal("0.90"),
        )
    )

    assert allowed.decision == "ALLOW"
    assert allowed.policy_version == "1.0.0"
    assert len(allowed.policy_hash) == 64
    assert denied.decision == "DENY"
    assert denied.checks[-5:] == (
        "tenant_mismatch",
        "role_missing",
        "scope_missing",
        "ownership_mismatch",
        "risk_above_policy",
    )


def test_checkpointed_workflow_recovers_and_compensates() -> None:
    definition = WorkflowDefinition(
        workflow_id="payment-settlement",
        version="1.0.0",
        steps=(
            WorkflowStep("authorize", "payment.authorize", "payment.release"),
            WorkflowStep("settle", "payment.settle", "payment.reverse"),
        ),
    )
    engine = DurableWorkflowEngine(InMemoryWorkflowStore())
    started = engine.start(
        definition,
        instance_id="workflow-1",
        tenant_id="tenant-a",
        context={"payment_id": "payment-1"},
    )
    running = engine.advance(
        definition, started.instance_id, step_result={"status": "COMPLETED"}
    )
    failed = engine.advance(
        definition, started.instance_id, step_result={"status": "FAILED"}
    )
    compensated = engine.compensate(started.instance_id)

    assert running.state == "RUNNING"
    assert failed.state == "COMPENSATING"
    assert engine.recover(started.instance_id) == compensated
    assert compensated.state == "COMPENSATED"


def test_sqlite_workflow_store_recovers_across_engine_instances(tmp_path) -> None:
    definition = WorkflowDefinition(
        workflow_id="tenant-onboarding",
        version="1.0.0",
        steps=(WorkflowStep("verify", "tenant.verify", "tenant.revoke"),),
    )
    path = tmp_path / "workflows.sqlite3"
    first_engine = DurableWorkflowEngine(SQLiteWorkflowStore(path))
    first_engine.start(
        definition,
        instance_id="workflow-durable",
        tenant_id="tenant-a",
        context={"application_id": "application-1"},
    )

    recovered = DurableWorkflowEngine(SQLiteWorkflowStore(path)).recover(
        "workflow-durable"
    )

    assert recovered.tenant_id == "tenant-a"
    assert recovered.context["application_id"] == "application-1"
    assert recovered.revision == 1


def test_error_budget_blocks_release_when_burning() -> None:
    objective = ServiceObjective(
        service="core-api",
        availability_target=0.9995,
        latency_p95_ms=300,
        window_days=30,
        rto_minutes=30,
        rpo_minutes=5,
    )

    assert evaluate_error_budget(
        objective, observed_requests=100_000, failed_requests=0
    ).release_allowed
    assert not evaluate_error_budget(
        objective, observed_requests=100_000, failed_requests=200
    ).release_allowed


def _production_plan() -> RolloutPlan:
    return RolloutPlan(
        release_id="release-1",
        source_environment="staging",
        target_environment="production",
        strategy="canary",
        canary_percent=5,
        approved_change=True,
        contract_validation=True,
        security_review=True,
        error_budget_available=True,
        rollback_verified=True,
        observability_ready=True,
        data_migration_safe=True,
    )


def test_progressive_rollout_promotes_or_rolls_back() -> None:
    assert evaluate_rollout(_production_plan()).next_canary_percent == 25
    assert (
        evaluate_rollout(_production_plan(), tenant_isolation_violation=True).status
        == "ROLLBACK"
    )


def test_feature_flags_are_tenant_scoped_and_expire() -> None:
    future = datetime.now(timezone.utc) + timedelta(days=1)
    flag = FeatureFlag(
        key="novapay-v2",
        owner="Payments Platform",
        tenant_ids=("tenant-a",),
        enabled=True,
        expires_at=future,
        rollout_percent=10,
    )

    assert flag_enabled(flag, tenant_id="tenant-a", allocation=5)
    assert not flag_enabled(flag, tenant_id="tenant-b", allocation=5)
    assert not flag_enabled(
        flag,
        tenant_id="tenant-a",
        allocation=5,
        now=future + timedelta(seconds=1),
    )


def test_data_residency_retention_and_deletion_are_enforced() -> None:
    policy = DataLifecyclePolicy(
        resource="payment_evidence",
        classification=DataClassification.RESTRICTED,
        retention=RetentionClass.AUDIT,
        allowed_regions=("AU",),
        deletion_requires_approval=True,
    )
    created = datetime(2010, 1, 1, tzinfo=timezone.utc)

    validate_residency(policy, "AU")
    with pytest.raises(ValueError, match="data_residency_violation"):
        validate_residency(policy, "US")
    assert not evaluate_deletion(policy, created_at=created, approved=False).allowed
    assert evaluate_deletion(policy, created_at=created, approved=True).allowed
