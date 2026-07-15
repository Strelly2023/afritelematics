CREATE TABLE IF NOT EXISTS mobility_event_outbox (
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

CREATE INDEX IF NOT EXISTS idx_mobility_event_outbox_claim
ON mobility_event_outbox (state, next_attempt_at);
