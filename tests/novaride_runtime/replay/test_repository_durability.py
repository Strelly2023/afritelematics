from __future__ import annotations

import asyncio
from dataclasses import asdict

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.replay.hashing import replay_plan_hash
from afritech.novaride_runtime.replay.models import ReplayPlanRecord
from afritech.novaride_runtime.replay.postgres_repository import PostgresReplayRepository


def test_replay_plan_survives_repository_restart(tmp_path) -> None:
    db_path = tmp_path / "novaride-replay.sqlite3"

    async def scenario() -> None:
        repo = PostgresReplayRepository(db_path)
        plan = ReplayPlanRecord(
            id=new_id("replay"),
            tenant_id="tenant-a",
            organization_id="org-a",
            workspace_id="workspace-a",
            name="Durable replay",
            description=None,
            scenario_type="correlation_id",
            source_reference="corr_api",
            target_environment="production",
            status="READY_FOR_EXECUTION",
            risk_level="medium",
            actions=({"action": "inspect"},),
            affected_resources=("booking-1",),
            validation_requirements=("hash",),
            rollback_plan={"mode": "shadow"},
            version=1,
            idempotency_key="idem-1",
            created_by="creator-1",
            created_at=utc_now().isoformat(),
            updated_by="creator-1",
            updated_at=utc_now().isoformat(),
        )
        plan = ReplayPlanRecord(**{**asdict(plan), "plan_hash": replay_plan_hash(plan)})
        await repo.create(plan)

        reopened = PostgresReplayRepository(db_path)
        loaded = await reopened.get(tenant_id="tenant-a", plan_id=plan.id)
        assert loaded is not None
        assert loaded.plan_hash == plan.plan_hash
        assert loaded.version == 1
        assert loaded.tenant_id == "tenant-a"
        assert await reopened.get(tenant_id="tenant-b", plan_id=plan.id) is None

    asyncio.run(scenario())
