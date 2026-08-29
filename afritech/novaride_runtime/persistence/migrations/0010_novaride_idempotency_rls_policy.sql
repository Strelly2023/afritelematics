-- NovaRide runtime idempotency tenant-isolation hardening.
--
-- idempotency_records already has ROW LEVEL SECURITY enabled.
-- This migration adds the missing tenant policy without modifying
-- the existing canonical table or replay-control-plane idempotency.
--
-- Runtime authority:
--   idempotency_records
--
-- Separate replay/control-plane authority:
--   novaride_runtime_idempotency

DROP POLICY IF EXISTS
    idempotency_records_tenant_isolation
    ON idempotency_records;

CREATE POLICY
    idempotency_records_tenant_isolation
    ON idempotency_records
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
