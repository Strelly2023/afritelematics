from __future__ import annotations

from pathlib import Path


def test_runtime_migrations_include_required_tables_and_rls() -> None:
    migration = Path(
        "afritech/novaride_runtime/persistence/migrations/0001_novaride_runtime.sql"
    ).read_text()
    rls = Path(
        "afritech/novaride_runtime/persistence/migrations/0002_novaride_runtime_rls.sql"
    ).read_text()
    replay = Path(
        "afritech/novaride_runtime/persistence/migrations/0007_novaride_replay_control_plane.sql"
    ).read_text()

    for table in [
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
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in rls

    for table in [
        "novaride_replay_plans",
        "novaride_replay_results",
        "novaride_replay_approvals",
        "novaride_replay_approval_votes",
        "novaride_replay_transitions",
        "novaride_runtime_idempotency",
        "novaride_runtime_audit",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in replay
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in replay


def test_resilience_hardening_migration_includes_durable_tables_indexes_and_outbox() -> None:
    migration = Path(
        "afritech/novaride_runtime/persistence/migrations/0008_novaride_resilience_hardening.sql"
    ).read_text()

    for table in [
        "novaride_offline_operations",
        "novaride_resilience_evidence",
        "novaride_provider_health",
        "novaride_provider_route_decisions",
        "novaride_sync_sessions",
        "novaride_sync_conflicts",
        "novaride_failover_events",
        "novaride_resilience_outbox",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in migration

    assert "UNIQUE (tenant_id, idempotency_key)" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_offline_operations_pending" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_resilience_outbox_claim" in migration
    assert "FOR UPDATE SKIP LOCKED" not in migration
