-- Durable, tenant-isolated rider and driver support workflow records.

CREATE TABLE IF NOT EXISTS support_cases (
    case_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL DEFAULT 1,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    subject_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    status TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    trip_id TEXT NULL,
    description TEXT NOT NULL DEFAULT '',
    CONSTRAINT support_cases_actor_type CHECK (actor_type IN ('RIDER', 'DRIVER'))
);

CREATE INDEX IF NOT EXISTS idx_support_cases_tenant ON support_cases (tenant_id);
CREATE INDEX IF NOT EXISTS idx_support_cases_trip ON support_cases (trip_id);
ALTER TABLE support_cases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS novaride_support_cases_tenant_isolation ON support_cases;
CREATE POLICY novaride_support_cases_tenant_isolation ON support_cases
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''))
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), ''));
