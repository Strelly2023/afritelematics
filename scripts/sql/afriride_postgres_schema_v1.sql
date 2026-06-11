BEGIN;

CREATE TABLE IF NOT EXISTS drivers (
    driver_id TEXT PRIMARY KEY,
    online BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS rides (
    ride_id TEXT PRIMARY KEY,
    passenger_id TEXT NOT NULL,
    pickup TEXT NOT NULL,
    destination TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'REQUESTED',
            'DRIVER_ASSIGNED',
            'IN_TRIP',
            'COMPLETED',
            'CANCELED',
            'REJECTED',
            'UNKNOWN'
        )
    ),
    assigned_driver TEXT,
    trace_hash TEXT,
    state_hash TEXT,
    events_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ride_events (
    event_id BIGSERIAL PRIMARY KEY,
    ride_id TEXT NOT NULL REFERENCES rides(ride_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ride_events_ride_id_event_id
    ON ride_events (ride_id, event_id);

CREATE TABLE IF NOT EXISTS trace_events (
    trace_row_id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    sequence_id BIGINT NOT NULL UNIQUE,
    device_id TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('rider', 'driver', 'operator')),
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    local_timestamp TIMESTAMPTZ NOT NULL,
    normalized_timestamp TIMESTAMPTZ NOT NULL,
    app_version TEXT NOT NULL,
    test_mode BOOLEAN NOT NULL,
    ride_id TEXT REFERENCES rides(ride_id) ON DELETE SET NULL,
    transition TEXT,
    previous_hash TEXT,
    event_hash TEXT NOT NULL UNIQUE,
    CONSTRAINT chk_trace_previous_hash_genesis
        CHECK (
            (sequence_id = 1 AND previous_hash IS NULL)
            OR (sequence_id > 1 AND previous_hash IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_trace_events_ride_id_sequence_id
    ON trace_events (ride_id, sequence_id);

CREATE INDEX IF NOT EXISTS idx_trace_events_actor_id
    ON trace_events (actor_id);

CREATE INDEX IF NOT EXISTS idx_trace_events_transition
    ON trace_events (transition);

CREATE TABLE IF NOT EXISTS idempotency_records (
    idempotency_key TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS replay_snapshots (
    ride_id TEXT PRIMARY KEY REFERENCES rides(ride_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (
        status IN (
            'REQUESTED',
            'DRIVER_ASSIGNED',
            'IN_TRIP',
            'COMPLETED',
            'CANCELED',
            'REJECTED',
            'UNKNOWN'
        )
    ),
    assigned_driver TEXT,
    passenger_id TEXT,
    transitions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_hash TEXT NOT NULL,
    replay_hash TEXT NOT NULL,
    replay_verified BOOLEAN NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_records (
    ride_id TEXT PRIMARY KEY REFERENCES rides(ride_id) ON DELETE CASCADE,
    trace_hash TEXT NOT NULL,
    replay_hash TEXT NOT NULL,
    verification_status TEXT NOT NULL CHECK (
        verification_status IN ('VERIFIED', 'REJECTED')
    ),
    receipt_id TEXT NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL,
    replay_snapshot_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS receipt_records (
    receipt_id TEXT PRIMARY KEY,
    ride_id TEXT NOT NULL UNIQUE REFERENCES rides(ride_id) ON DELETE CASCADE,
    replay_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (
        status IN (
            'REQUESTED',
            'DRIVER_ASSIGNED',
            'IN_TRIP',
            'COMPLETED',
            'CANCELED',
            'REJECTED',
            'UNKNOWN'
        )
    ),
    trace_hash TEXT NOT NULL,
    replay_hash TEXT NOT NULL,
    receipt_hash TEXT NOT NULL UNIQUE,
    issued_at TIMESTAMPTZ NOT NULL
);

COMMIT;
