-- NovaRide RiderProfile persistence tenant-isolation hardening.
--
-- Historical migration 0002 enabled ROW LEVEL SECURITY on rider_profiles
-- but did not install an active tenant policy.
--
-- This additive migration supplies the missing policy authority without
-- rewriting historical migration lineage.
--
-- Canonical NovaRide tenant authority:
--
--   app.tenant_id
--
-- USING protects reads/updates/deletes.
-- WITH CHECK protects inserts/updates.
--
-- Missing app.tenant_id is intentionally fail-closed because
-- current_setting(..., true) returns NULL and tenant equality does not
-- evaluate TRUE.

ALTER TABLE rider_profiles
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS
    novaride_rider_profiles_tenant_isolation
    ON rider_profiles;

CREATE POLICY
    novaride_rider_profiles_tenant_isolation
    ON rider_profiles
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
