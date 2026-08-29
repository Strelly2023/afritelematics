-- NovaRide Operations Workspace durable auxiliary persistence.
--
-- This authority is intentionally separate from rider/driver support_cases.
-- It supports the Operations Support responsibility without expanding the
-- canonical RuntimeRepositories contract.

CREATE TABLE IF NOT EXISTS novaride_operations_records (
    record_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    region_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_key TEXT NOT NULL,
    state TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (tenant_id, record_type, record_key)
);

CREATE INDEX IF NOT EXISTS
    idx_novaride_operations_records_tenant_type_updated
ON novaride_operations_records (
    tenant_id,
    record_type,
    updated_at DESC
);

CREATE INDEX IF NOT EXISTS
    idx_novaride_operations_records_tenant_region_type
ON novaride_operations_records (
    tenant_id,
    region_id,
    record_type
);

ALTER TABLE novaride_operations_records
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS
    novaride_operations_records_tenant_isolation
ON novaride_operations_records;

CREATE POLICY
    novaride_operations_records_tenant_isolation
ON novaride_operations_records
USING (
    tenant_id = NULLIF(
        current_setting(
            'app.current_tenant_id',
            true
        ),
        ''
    )
)
WITH CHECK (
    tenant_id = NULLIF(
        current_setting(
            'app.current_tenant_id',
            true
        ),
        ''
    )
);
