CREATE TABLE IF NOT EXISTS operational_verification_programs (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, organization_id TEXT NOT NULL, release_id TEXT NOT NULL, environment TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS operational_verification_runs (id TEXT PRIMARY KEY, program_id TEXT NOT NULL, tenant_id TEXT NOT NULL, region TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS capability_verifications (id TEXT PRIMARY KEY, program_id TEXT NOT NULL, domain TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS verification_checks (id TEXT PRIMARY KEY, capability_id TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS verification_findings (id TEXT PRIMARY KEY, check_id TEXT NOT NULL, severity TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS verification_metrics (id TEXT PRIMARY KEY, check_id TEXT NOT NULL, metric_name TEXT NOT NULL, metric_value_numeric NUMERIC, payload JSONB NOT NULL);
