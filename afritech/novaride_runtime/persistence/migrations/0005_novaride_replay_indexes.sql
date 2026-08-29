CREATE TABLE IF NOT EXISTS novaride_event_replay_plans (
    replay_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    region_code TEXT,
    mode TEXT NOT NULL,
    scope JSONB NOT NULL,
    operator_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    approval_reference TEXT,
    state TEXT NOT NULL,
    source_state_hash TEXT,
    replay_state_hash TEXT,
    matched BOOLEAN,
    evidence_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mobility_events_aggregate_version
ON mobility_events (tenant_id, aggregate_id, aggregate_version, event_type);

CREATE INDEX IF NOT EXISTS idx_mobility_events_tenant_region_time
ON mobility_events (tenant_id, region_code, occurred_at);

CREATE INDEX IF NOT EXISTS idx_novaride_replay_scope
ON novaride_event_replay_plans USING gin (scope);
