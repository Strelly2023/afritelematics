-- NovaRide projection persistence RLS hardening.
--
-- Projection tables contain tenant-scoped derived state. They are not
-- authoritative business aggregates, but tenant isolation is still mandatory.
--
-- This migration is intentionally additive. Migration 0004 remains immutable.

ALTER TABLE novaride_projection_state
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE novaride_projection_versions
    ENABLE ROW LEVEL SECURITY;


DROP POLICY IF EXISTS
    novaride_projection_state_tenant_isolation
    ON novaride_projection_state;

CREATE POLICY
    novaride_projection_state_tenant_isolation
    ON novaride_projection_state
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
    novaride_projection_versions_tenant_isolation
    ON novaride_projection_versions;

CREATE POLICY
    novaride_projection_versions_tenant_isolation
    ON novaride_projection_versions
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
