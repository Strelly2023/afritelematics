ALTER TABLE novaid_authentication_sessions
 ADD COLUMN IF NOT EXISTS membership_id uuid REFERENCES novaid_tenant_memberships,
 ADD COLUMN IF NOT EXISTS authenticated_at timestamptz,
 ADD COLUMN IF NOT EXISTS idle_expires_at timestamptz,
 ADD COLUMN IF NOT EXISTS absolute_expires_at timestamptz,
 ADD COLUMN IF NOT EXISTS pending_mfa_expires_at timestamptz,
 ADD COLUMN IF NOT EXISTS step_up_expires_at timestamptz,
 ADD COLUMN IF NOT EXISTS locked_at timestamptz,
 ADD COLUMN IF NOT EXISTS expired_at timestamptz,
 ADD COLUMN IF NOT EXISTS compromised_at timestamptz,
 ADD COLUMN IF NOT EXISTS network_reference text,
 ADD COLUMN IF NOT EXISTS authentication_methods jsonb NOT NULL DEFAULT '[]'::jsonb,
 ADD COLUMN IF NOT EXISTS security_version integer NOT NULL DEFAULT 1,
 ADD COLUMN IF NOT EXISTS revoked_by uuid,
 ADD COLUMN IF NOT EXISTS compromise_reason text;

UPDATE novaid_authentication_sessions
SET authenticated_at=COALESCE(authenticated_at,authentication_time),
    absolute_expires_at=COALESCE(absolute_expires_at,expires_at),
    idle_expires_at=COALESCE(idle_expires_at,last_seen_at + interval '30 minutes'),
    pending_mfa_expires_at=CASE WHEN status='PENDING_MFA'
      THEN COALESCE(pending_mfa_expires_at,created_at + interval '5 minutes')
      ELSE pending_mfa_expires_at END;

ALTER TABLE novaid_security_outbox
 ADD COLUMN IF NOT EXISTS available_at timestamptz,
 ADD COLUMN IF NOT EXISTS last_attempt_at timestamptz,
 ADD COLUMN IF NOT EXISTS lease_owner text,
 ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz;
ALTER TABLE novaid_security_outbox DROP CONSTRAINT IF EXISTS novaid_security_outbox_status_check;
ALTER TABLE novaid_security_outbox ADD CONSTRAINT novaid_security_outbox_status_check
 CHECK(status IN ('PENDING','PUBLISHING','PUBLISHED','FAILED','DEAD_LETTER'));
UPDATE novaid_security_outbox SET available_at=COALESCE(available_at,created_at);

CREATE INDEX IF NOT EXISTS ix_novaid_session_lifecycle
ON novaid_authentication_sessions(tenant_id,status,idle_expires_at,absolute_expires_at);
CREATE INDEX IF NOT EXISTS ix_novaid_outbox_lease
ON novaid_security_outbox(status,available_at,lease_expires_at);

INSERT INTO novaid_schema_migrations(revision) VALUES ('0003_novaid_session_lifecycle.sql')
ON CONFLICT(revision) DO NOTHING;
