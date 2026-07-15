CREATE INDEX IF NOT EXISTS idx_ov_programs_tenant_release ON operational_verification_programs (tenant_id, release_id);
CREATE INDEX IF NOT EXISTS idx_ov_runs_program ON operational_verification_runs (program_id);
CREATE INDEX IF NOT EXISTS idx_evidence_release_status ON evidence_envelopes (release_id, status);
CREATE INDEX IF NOT EXISTS idx_prr_release ON prr_packages (release_id);
CREATE INDEX IF NOT EXISTS idx_payment_release_state ON payment_activation_assessments (release_id, state);
CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, event_type TEXT NOT NULL, aggregate_id TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS idempotency_records (key TEXT PRIMARY KEY, scope TEXT NOT NULL, response_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
