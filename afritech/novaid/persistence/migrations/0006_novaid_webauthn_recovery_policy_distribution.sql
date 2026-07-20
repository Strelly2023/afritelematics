ALTER TABLE novaid_recovery_codes DROP CONSTRAINT IF EXISTS novaid_recovery_codes_status_check;
ALTER TABLE novaid_recovery_codes ADD CONSTRAINT novaid_recovery_codes_status_check
 CHECK(status IN ('ACTIVE','USED','REVOKED','EXPIRED','SUPERSEDED'));
ALTER TABLE novaid_recovery_codes
 ADD COLUMN IF NOT EXISTS batch_id uuid,
 ADD COLUMN IF NOT EXISTS used_at timestamptz,
 ADD COLUMN IF NOT EXISTS revoked_at timestamptz,
 ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count >= 0);

CREATE TABLE IF NOT EXISTS novaid_recovery_code_batches(
 batch_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities,
 status text NOT NULL CHECK(status IN ('ACTIVE','REVOKED','SUPERSEDED','EXPIRED')),
 created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
 revoked_at timestamptz, version integer NOT NULL DEFAULT 1 CHECK(version > 0),
 CHECK(expires_at > created_at));
ALTER TABLE novaid_recovery_codes DROP CONSTRAINT IF EXISTS novaid_recovery_codes_batch_id_fkey;
ALTER TABLE novaid_recovery_codes ADD CONSTRAINT novaid_recovery_codes_batch_id_fkey
 FOREIGN KEY(batch_id) REFERENCES novaid_recovery_code_batches;
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_batches_identity
 ON novaid_recovery_code_batches(tenant_id,identity_id,status,expires_at);
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_codes_batch
 ON novaid_recovery_codes(batch_id,status,expires_at);

ALTER TABLE novaid_account_recovery_requests DROP CONSTRAINT IF EXISTS novaid_account_recovery_requests_status_check;
ALTER TABLE novaid_account_recovery_requests ADD CONSTRAINT novaid_account_recovery_requests_status_check
 CHECK(status IN ('REQUESTED','UNDER_REVIEW','CHALLENGE_ISSUED','VERIFIED','APPROVED',
 'REJECTED','COMPLETED','CANCELLED','EXPIRED'));
ALTER TABLE novaid_account_recovery_requests
 ADD COLUMN IF NOT EXISTS recovery_method text,
 ADD COLUMN IF NOT EXISTS correlation_id text,
 ADD COLUMN IF NOT EXISTS request_id text,
 ADD COLUMN IF NOT EXISTS device_reference text,
 ADD COLUMN IF NOT EXISTS network_reference text,
 ADD COLUMN IF NOT EXISTS rejected_at timestamptz,
 ADD COLUMN IF NOT EXISTS cancelled_at timestamptz;

CREATE TABLE IF NOT EXISTS novaid_account_recovery_approvals(
 approval_id uuid PRIMARY KEY, recovery_request_id uuid NOT NULL REFERENCES novaid_account_recovery_requests,
 tenant_id uuid NOT NULL REFERENCES novaid_tenants, approver_identity_id uuid NOT NULL REFERENCES novaid_identities,
 decision text NOT NULL CHECK(decision IN ('APPROVED','REJECTED')),
 reason text NOT NULL, created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
 UNIQUE(recovery_request_id,approver_identity_id), CHECK(expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_approvals_request
 ON novaid_account_recovery_approvals(tenant_id,recovery_request_id,decision,created_at);

CREATE TABLE IF NOT EXISTS novaid_account_recovery_evidence(
 evidence_id uuid PRIMARY KEY, recovery_request_id uuid NOT NULL REFERENCES novaid_account_recovery_requests,
 tenant_id uuid NOT NULL REFERENCES novaid_tenants, identity_id uuid NOT NULL REFERENCES novaid_identities,
 method text NOT NULL, result text NOT NULL CHECK(result IN ('VERIFIED','REJECTED')),
 risk_indicators jsonb NOT NULL DEFAULT '[]'::jsonb, actor_identity_id uuid,
 correlation_id text NOT NULL, request_id text NOT NULL, created_at timestamptz NOT NULL);
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_evidence_request
 ON novaid_account_recovery_evidence(tenant_id,recovery_request_id,created_at);

CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policy_history(
 policy_history_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 policy_version integer NOT NULL CHECK(policy_version > 0), status text NOT NULL
 CHECK(status IN ('DRAFT','ACTIVE','SUPERSEDED','REVOKED')), policy jsonb NOT NULL,
 reason text NOT NULL, created_at timestamptz NOT NULL, created_by uuid NOT NULL,
 UNIQUE(tenant_id,policy_version));

ALTER TABLE novaid_tenant_webauthn_policies
 ADD COLUMN IF NOT EXISTS passkeys_enabled boolean NOT NULL DEFAULT true,
 ADD COLUMN IF NOT EXISTS passwordless_enabled boolean NOT NULL DEFAULT true,
 ADD COLUMN IF NOT EXISTS recovery_codes_enabled boolean NOT NULL DEFAULT true,
 ADD COLUMN IF NOT EXISTS recovery_code_count integer NOT NULL DEFAULT 8 CHECK(recovery_code_count BETWEEN 1 AND 20),
 ADD COLUMN IF NOT EXISTS recovery_code_expiry_days integer NOT NULL DEFAULT 365 CHECK(recovery_code_expiry_days > 0),
 ADD COLUMN IF NOT EXISTS recovery_approval_count integer NOT NULL DEFAULT 1 CHECK(recovery_approval_count > 0),
 ADD COLUMN IF NOT EXISTS recovery_requires_new_authenticator boolean NOT NULL DEFAULT true;

CREATE TABLE IF NOT EXISTS novaid_webauthn_challenge_coordination(
 coordination_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 challenge_id uuid NOT NULL, purpose text NOT NULL, status text NOT NULL
 CHECK(status IN ('ACTIVE','CONSUMED','SUPERSEDED','EXPIRED')),
 challenge_version integer NOT NULL CHECK(challenge_version > 0),
 created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
 consumed_at timestamptz, UNIQUE(tenant_id,challenge_id), CHECK(expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_challenge_coordination
 ON novaid_webauthn_challenge_coordination(tenant_id,status,expires_at,challenge_version);

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0006_novaid_webauthn_recovery_policy_distribution.sql') ON CONFLICT(revision) DO NOTHING;
