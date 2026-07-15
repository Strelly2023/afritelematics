#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from afritech.novaride_runtime.events.replay_planner import ReplayMode, plan_replay
from afritech.novaride_runtime.events.replay_verifier import verify_replay
from afritech.novaride_runtime.models import ActorType, RuntimeContext
from afritech.novaride_runtime.services import create_runtime


REPORT = ROOT / "reports" / "novaride" / "deployment" / "live-runtime-verification.yaml"


def main() -> int:
    runtime = create_runtime()
    ctx = RuntimeContext("tenant_verify", "org_verify", "AU", ActorType.SYSTEM, "verify", correlation_id="corr_verify_live")
    runtime.events.emit(ctx, event_type="BookingCreated", aggregate_id="booking_verify", aggregate_type="Booking", aggregate_version=1, payload={"source": "verification"})
    plan = plan_replay(mode=ReplayMode.CORRELATION_ID, scope={"correlation_id": "corr_verify_live"}, operator_id="verify", reason="live verification dry run")
    result = verify_replay(replay_id=plan.replay_id, events=runtime.repositories.events.by_correlation("corr_verify_live"))
    report = {
        "status": "CERTIFICATION_INCOMPLETE",
        "api_reachable": "local_runtime_constructed",
        "health_200": False,
        "live_200": False,
        "ready_200": False,
        "postgresql_reachable": False,
        "migration_version_current": "static_contract_only",
        "outbox_worker_healthy": False,
        "consumer_worker_healthy": False,
        "projection_worker_healthy": False,
        "replay_worker_healthy": "local_verifier_available",
        "test_event_published": True,
        "test_event_consumed": False,
        "projection_updated": False,
        "replay_succeeds": result.matched,
        "replay_hashes_match": result.matched,
        "replay_side_effects_blocked": result.side_effects_blocked,
        "metrics_exposed": False,
        "tracing_present": False,
        "reason": "no live deployment endpoint, database, or worker processes were provided in this environment",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(yaml.safe_dump(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
