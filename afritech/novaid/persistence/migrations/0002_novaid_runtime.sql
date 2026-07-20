CREATE TABLE IF NOT EXISTS novaid_schema_migrations (
 revision text PRIMARY KEY,
 applied_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO novaid_schema_migrations(revision) VALUES ('0001_identity_core.sql')
ON CONFLICT(revision) DO NOTHING;

CREATE TABLE IF NOT EXISTS novaid_security_outbox (
 outbox_id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 event_type text NOT NULL,
 resource_type text NOT NULL,
 resource_id uuid NOT NULL,
 event_version integer NOT NULL,
 payload jsonb NOT NULL,
 created_at timestamptz NOT NULL,
 published_at timestamptz,
 attempt_count integer NOT NULL DEFAULT 0,
 last_error text,
 next_attempt_at timestamptz,
 status text NOT NULL CHECK(status IN ('PENDING','PUBLISHED','FAILED','DEAD_LETTER'))
);
CREATE INDEX IF NOT EXISTS ix_novaid_outbox_pending
ON novaid_security_outbox(status,next_attempt_at,created_at);

INSERT INTO novaid_schema_migrations(revision) VALUES ('0002_novaid_runtime.sql')
ON CONFLICT(revision) DO NOTHING;
