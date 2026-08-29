-- NR-CAP-001 Rider Lifecycle persistence tenant isolation.
--
-- R18-I6-CAP001-C2B-R4A
--
-- Historical migration 0002 enabled RLS on fare_quotes and bookings
-- but did not install active tenant policies.
--
-- This additive migration supplies the missing active policy authority
-- without rewriting historical migration lineage.
--
-- Missing app.tenant_id is intentionally fail-closed because
-- current_setting(..., true) returns NULL and tenant equality does not
-- evaluate TRUE.

DROP POLICY IF EXISTS
    novaride_fare_quotes_tenant_isolation
    ON fare_quotes;

CREATE POLICY
    novaride_fare_quotes_tenant_isolation
    ON fare_quotes
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
    novaride_bookings_tenant_isolation
    ON bookings;

CREATE POLICY
    novaride_bookings_tenant_isolation
    ON bookings
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
