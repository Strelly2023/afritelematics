ALTER TABLE novaid_webauthn_outbox
 ADD COLUMN IF NOT EXISTS correlation_id text NOT NULL DEFAULT '',
 ADD COLUMN IF NOT EXISTS request_id text NOT NULL DEFAULT '',
 ADD COLUMN IF NOT EXISTS resource_type text NOT NULL DEFAULT 'WEBAUTHN_CREDENTIAL',
 ADD COLUMN IF NOT EXISTS lease_owner text,
 ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz,
 ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz,
 ADD COLUMN IF NOT EXISTS last_attempt_at timestamptz,
 ADD COLUMN IF NOT EXISTS last_error text,
 ADD COLUMN IF NOT EXISTS dead_letter_reason text;
ALTER TABLE novaid_webauthn_outbox DROP CONSTRAINT IF EXISTS novaid_webauthn_outbox_status_check;
ALTER TABLE novaid_webauthn_outbox ADD CONSTRAINT novaid_webauthn_outbox_status_check
 CHECK(status IN ('PENDING','PUBLISHING','PUBLISHED','FAILED','DEAD_LETTER'));
CREATE INDEX IF NOT EXISTS ix_novaid_webauthn_outbox_lease
 ON novaid_webauthn_outbox(status,available_at,lease_expires_at,next_attempt_at);

ALTER TABLE novaid_webauthn_event_checkpoints
 ADD COLUMN IF NOT EXISTS resource_type text NOT NULL DEFAULT '',
 ADD COLUMN IF NOT EXISTS resource_reference text NOT NULL DEFAULT '',
 ADD COLUMN IF NOT EXISTS last_event_id text,
 ADD COLUMN IF NOT EXISTS applied_at timestamptz;

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0007_novaid_webauthn_distributed_runtime.sql') ON CONFLICT(revision) DO NOTHING;
