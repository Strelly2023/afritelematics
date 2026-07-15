CREATE TABLE IF NOT EXISTS prr_packages (prr_id TEXT PRIMARY KEY, release_id TEXT NOT NULL, status TEXT NOT NULL, evidence_manifest_hash TEXT NOT NULL, payload JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS prr_domain_results (id TEXT PRIMARY KEY, prr_id TEXT NOT NULL, domain TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
