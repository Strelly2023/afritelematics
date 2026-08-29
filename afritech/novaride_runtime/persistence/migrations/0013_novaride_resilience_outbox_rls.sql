-- NovaRide resilience-outbox tenant isolation.
--
-- Migration 0008 owns the resilience-outbox schema and RLS enablement.
-- Migration 0012 owns the seven resilience state-authority policies.
-- This migration owns only the resilience publication-outbox policy.
--
-- Missing app.tenant_id is intentionally fail-closed.

ALTER TABLE novaride_resilience_outbox
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS
    novaride_resilience_outbox_tenant_isolation
    ON novaride_resilience_outbox;

CREATE POLICY
    novaride_resilience_outbox_tenant_isolation
    ON novaride_resilience_outbox
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
