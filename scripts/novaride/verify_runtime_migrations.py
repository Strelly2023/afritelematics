#!/usr/bin/env python3
"""Verify NovaRide runtime migration contracts.

This script performs static verification by default. If NOVARIDE_POSTGRES_DSN is
provided, deployment automation can extend it to execute against a temporary
PostgreSQL database.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "afritech" / "novaride_runtime" / "persistence" / "migrations"
REPORT = ROOT / "reports" / "novaride" / "deployment" / "runtime-migration-verification.json"

REQUIRED_TABLES = {
    "rider_profiles",
    "driver_profiles",
    "driver_eligibility",
    "driver_availability",
    "driver_shifts",
    "driver_offers",
    "driver_bids",
    "bookings",
    "trips",
    "trip_locations",
    "fare_quotes",
    "operator_commands",
    "incidents",
    "emergencies",
    "fleets",
    "fleet_drivers",
    "fleet_vehicles",
    "fleet_schedules",
    "fleet_compliance",
    "delivery_orders",
    "delivery_stops",
    "corporate_accounts",
    "corporate_travel_policies",
    "corporate_bookings",
    "transit_routes",
    "transit_stops",
    "transit_journeys",
    "mobility_events",
    "event_replay_checkpoints",
    "idempotency_records",
    "read_model_checkpoints",
    "mobility_event_outbox",
    "novaride_projection_state",
    "novaride_replay_plans",
}


def main() -> int:
    sql = "\n".join(path.read_text() for path in sorted(MIGRATIONS.glob("*.sql")))
    missing_tables = sorted(table for table in REQUIRED_TABLES if f"CREATE TABLE IF NOT EXISTS {table}" not in sql)
    report = {
        "status": "PASS" if not missing_tables else "FAIL",
        "mode": "static_contract_verification",
        "live_postgres_dsn_present": bool(os.environ.get("NOVARIDE_POSTGRES_DSN")),
        "live_postgres_applied": False,
        "required_tables": sorted(REQUIRED_TABLES),
        "missing_tables": missing_tables,
        "indexes_declared": "CREATE INDEX" in sql or "CREATE UNIQUE INDEX" in sql,
        "rls_declared": "ENABLE ROW LEVEL SECURITY" in sql,
        "unique_constraints_declared": "UNIQUE" in sql,
        "event_immutability_declared": "preventing UPDATE/DELETE on" in sql,
        "rollback_behavior_verified": False,
        "reason": "live PostgreSQL verification requires NOVARIDE_POSTGRES_DSN and isolated database execution",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
