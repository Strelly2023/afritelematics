CREATE TABLE IF NOT EXISTS digital_ux_twin_profiles (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, release_id TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS digital_ux_twin_runs (id TEXT PRIMARY KEY, profile_id TEXT NOT NULL, scenario TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS telemetry_ingestion_checkpoints (id TEXT PRIMARY KEY, profile_id TEXT NOT NULL, source TEXT NOT NULL, status TEXT NOT NULL, last_seen_at TIMESTAMPTZ, payload JSONB NOT NULL);
