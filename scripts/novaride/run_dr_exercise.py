#!/usr/bin/env python3
"""Generate NovaRide DR exercise evidence.

This script is non-destructive by default. Destructive production exercises
require --authorize-production-destructive.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


EXERCISES = {
    "availability-zone-loss",
    "database-primary-failure",
    "kafka-broker-loss",
    "payment-provider-outage",
    "maps-provider-outage",
    "notification-provider-outage",
    "network-partition",
    "regional-control-plane-isolation",
    "offline-queue-replay",
    "emergency-path-verification",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise", required=True, choices=sorted(EXERCISES))
    parser.add_argument("--environment", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--output", default="reports/novaride/dr")
    parser.add_argument("--destructive", action="store_true")
    parser.add_argument("--authorize-production-destructive", action="store_true")
    args = parser.parse_args()

    if (
        args.environment == "production"
        and args.destructive
        and not args.authorize_production_destructive
    ):
        raise SystemExit("refusing_destructive_production_dr_exercise_without_authorization")

    now = datetime.now(UTC).isoformat()
    package = {
        "exercise_id": f"{args.exercise}-{now}",
        "environment": args.environment,
        "region": args.region,
        "start_time": now,
        "detection_time": now,
        "failover_time": None,
        "recovery_time": now,
        "measured_data_loss": "not_measured_dry_run",
        "rto_result": "not_live_tested",
        "rpo_result": "not_live_tested",
        "failed_controls": [],
        "corrective_actions": [],
        "logs": [],
        "traces": [],
        "metrics_snapshot": {},
        "operator_approvals": [],
        "final_verdict": "DRY_RUN_EVIDENCE_GENERATED",
    }
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.exercise}.json"
    output_path.write_text(json.dumps(package, indent=2, sort_keys=True))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
