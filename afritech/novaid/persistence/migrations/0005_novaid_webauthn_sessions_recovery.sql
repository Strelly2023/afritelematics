ALTER TABLE novaid_authentication_sessions
 ADD COLUMN IF NOT EXISTS step_up_completed_at timestamptz,
 ADD COLUMN IF NOT EXISTS step_up_credential_id text,
 ADD COLUMN IF NOT EXISTS credential_assurance_level text;

CREATE TABLE IF NOT EXISTS novaid_webauthn_session_assertions(
 assertion_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities, session_id uuid NOT NULL REFERENCES novaid_authentication_sessions,
 credential_id text NOT NULL REFERENCES novaid_webauthn_credentials,
 purpose text NOT NULL CHECK(purpose IN ('PASSWORDLESS','STEP_UP','MFA')),
 authentication_strength text NOT NULL, user_verified boolean NOT NULL,
 created_at timestamptz NOT NULL, expires_at timestamptz,
 CHECK(expires_at IS NULL OR expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_webauthn_assertion_tenant_session
 ON novaid_webauthn_session_assertions(tenant_id,session_id,created_at);

CREATE TABLE IF NOT EXISTS novaid_recovery_codes(
 recovery_code_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities, code_hash text NOT NULL UNIQUE,
 status text NOT NULL CHECK(status IN ('ACTIVE','CONSUMED','REVOKED')),
 created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL, consumed_at timestamptz,
 version integer NOT NULL DEFAULT 1 CHECK(version > 0), CHECK(expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_codes_identity
 ON novaid_recovery_codes(tenant_id,identity_id,status,expires_at);

CREATE TABLE IF NOT EXISTS novaid_account_recovery_requests(
 recovery_request_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities,
 status text NOT NULL CHECK(status IN ('PENDING','APPROVED','DENIED','COMPLETED','EXPIRED')),
 requested_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
 approved_at timestamptz, approved_by uuid, completed_at timestamptz,
 reason text NOT NULL, version integer NOT NULL DEFAULT 1 CHECK(version > 0),
 CHECK(expires_at > requested_at));
CREATE INDEX IF NOT EXISTS ix_novaid_account_recovery_state
 ON novaid_account_recovery_requests(tenant_id,identity_id,status,requested_at);

CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policies(
 tenant_id uuid PRIMARY KEY REFERENCES novaid_tenants, require_webauthn boolean NOT NULL DEFAULT false,
 require_phishing_resistant_step_up boolean NOT NULL DEFAULT false,
 user_verification text NOT NULL CHECK(user_verification IN ('required','preferred','discouraged')),
 attestation text NOT NULL CHECK(attestation IN ('none','indirect','direct','enterprise')),
 maximum_credentials integer NOT NULL DEFAULT 10 CHECK(maximum_credentials > 0),
 step_up_seconds integer NOT NULL DEFAULT 300 CHECK(step_up_seconds > 0),
 updated_at timestamptz NOT NULL, updated_by uuid, version integer NOT NULL DEFAULT 1 CHECK(version > 0));

CREATE TABLE IF NOT EXISTS novaid_webauthn_outbox(
 outbox_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 event_type text NOT NULL, resource_id text NOT NULL, event_version integer NOT NULL CHECK(event_version > 0),
 payload jsonb NOT NULL, status text NOT NULL CHECK(status IN ('PENDING','PUBLISHING','PUBLISHED','FAILED','DEAD_LETTER')),
 created_at timestamptz NOT NULL, available_at timestamptz NOT NULL, published_at timestamptz,
 attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count >= 0), version integer NOT NULL DEFAULT 1 CHECK(version > 0));
CREATE INDEX IF NOT EXISTS ix_novaid_webauthn_outbox_delivery
 ON novaid_webauthn_outbox(status,available_at,created_at);

CREATE TABLE IF NOT EXISTS novaid_webauthn_event_checkpoints(
 consumer_name text NOT NULL, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 event_version integer NOT NULL CHECK(event_version >= 0), updated_at timestamptz NOT NULL,
 PRIMARY KEY(consumer_name,tenant_id));

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0005_novaid_webauthn_sessions_recovery.sql') ON CONFLICT(revision) DO NOTHING;
