CREATE TABLE IF NOT EXISTS novaride_projection_state (
    projection_name TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    checkpoint BIGINT NOT NULL DEFAULT 0,
    last_event_id TEXT,
    last_event_timestamp TIMESTAMPTZ,
    state_hash TEXT,
    rebuild_status TEXT NOT NULL,
    lag_seconds NUMERIC(12,3) NOT NULL DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (projection_name, tenant_id, region_code)
);

CREATE TABLE IF NOT EXISTS novaride_projection_versions (
    projection_version_id TEXT PRIMARY KEY,
    projection_name TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    state_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
