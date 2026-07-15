CREATE TABLE IF NOT EXISTS novaride_offline_operations (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    encrypted_payload JSONB NOT NULL,
    payload_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    authority_required BOOLEAN NOT NULL DEFAULT FALSE,
    conflict_policy TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ,
    last_error_code TEXT,
    priority TEXT NOT NULL DEFAULT 'NORMAL',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_offline_operations_pending
ON novaride_offline_operations (
    tenant_id,
    region_code,
    status,
    next_attempt_at
);

CREATE TABLE IF NOT EXISTS novaride_resilience_evidence (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    capability TEXT NOT NULL,
    degraded_mode TEXT NOT NULL,
    decision TEXT NOT NULL,
    fallback_used TEXT,
    evidence JSONB NOT NULL,
    correlation_id TEXT,
    evidence_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS novaride_provider_health (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    provider TEXT NOT NULL,
    capability TEXT NOT NULL,
    state TEXT NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    error_rate NUMERIC NOT NULL DEFAULT 0,
    timeout_rate NUMERIC NOT NULL DEFAULT 0,
    success_rate NUMERIC NOT NULL DEFAULT 1,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    consecutive_successes INTEGER NOT NULL DEFAULT 0,
    last_successful_probe_at TIMESTAMPTZ,
    last_state_transition_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provider_health_latest
ON novaride_provider_health (tenant_id, region_code, capability, provider, updated_at DESC);

CREATE TABLE IF NOT EXISTS novaride_provider_route_decisions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    capability TEXT NOT NULL,
    selected_provider TEXT,
    attempted_providers JSONB NOT NULL,
    degraded_mode TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS novaride_sync_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    device_id TEXT NOT NULL,
    last_server_cursor TEXT,
    server_cursor TEXT NOT NULL,
    status TEXT NOT NULL,
    operation_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS novaride_sync_conflicts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    sync_session_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    local_version INTEGER NOT NULL,
    server_version INTEGER NOT NULL,
    policy_selected TEXT NOT NULL,
    winner TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS novaride_failover_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    previous_state TEXT NOT NULL,
    target_state TEXT NOT NULL,
    reason TEXT NOT NULL,
    automatic BOOLEAN NOT NULL DEFAULT FALSE,
    approval_reference TEXT,
    evidence_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS novaride_resilience_outbox (
    outbox_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL,
    region_code TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('PENDING','CLAIMED','PUBLISHED','FAILED','DEAD_LETTERED')),
    worker_id TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    broker_ack TEXT,
    last_error TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resilience_outbox_claim
ON novaride_resilience_outbox (state, next_attempt_at);

ALTER TABLE novaride_offline_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_resilience_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_provider_health ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_provider_route_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_sync_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_sync_conflicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_failover_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_resilience_outbox ENABLE ROW LEVEL SECURITY;
