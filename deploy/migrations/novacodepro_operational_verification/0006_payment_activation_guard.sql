CREATE TABLE IF NOT EXISTS payment_activation_assessments (id TEXT PRIMARY KEY, release_id TEXT NOT NULL, provider TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'DISABLED', payload JSONB NOT NULL);
