-- NovaRide resilience persistence tenant-isolation hardening.
--
-- Migration 0008 creates the resilience persistence authorities and
-- enables ROW LEVEL SECURITY, but does not install tenant policies.
--
-- This additive migration installs the canonical NovaRide tenant policy
-- convention:
--
--   tenant_id = current_setting('app.tenant_id', true)
--
-- USING protects reads/updates/deletes.
-- WITH CHECK protects inserts/updates.
--
-- Missing tenant context remains fail-closed because
-- current_setting(..., true) returns NULL when unset and the comparison
-- therefore does not evaluate TRUE.
--
-- Migration 0008 remains immutable.

ALTER TABLE novaride_offline_operations
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_resilience_evidence
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_provider_health
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_provider_route_decisions
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_sync_sessions
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_sync_conflicts
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_failover_events
    ENABLE ROW LEVEL SECURITY;


DROP POLICY IF EXISTS
    novaride_offline_operations_tenant_isolation
    ON novaride_offline_operations;

CREATE POLICY
    novaride_offline_operations_tenant_isolation
    ON novaride_offline_operations
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_resilience_evidence_tenant_isolation
    ON novaride_resilience_evidence;

CREATE POLICY
    novaride_resilience_evidence_tenant_isolation
    ON novaride_resilience_evidence
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_provider_health_tenant_isolation
    ON novaride_provider_health;

CREATE POLICY
    novaride_provider_health_tenant_isolation
    ON novaride_provider_health
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_provider_route_decisions_tenant_isolation
    ON novaride_provider_route_decisions;

CREATE POLICY
    novaride_provider_route_decisions_tenant_isolation
    ON novaride_provider_route_decisions
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_sync_sessions_tenant_isolation
    ON novaride_sync_sessions;

CREATE POLICY
    novaride_sync_sessions_tenant_isolation
    ON novaride_sync_sessions
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_sync_conflicts_tenant_isolation
    ON novaride_sync_conflicts;

CREATE POLICY
    novaride_sync_conflicts_tenant_isolation
    ON novaride_sync_conflicts
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );


DROP POLICY IF EXISTS
    novaride_failover_events_tenant_isolation
    ON novaride_failover_events;

CREATE POLICY
    novaride_failover_events_tenant_isolation
    ON novaride_failover_events
    USING (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    )
    WITH CHECK (
        tenant_id = current_setting(
            'app.tenant_id',
            true
        )
    );
