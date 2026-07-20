CREATE TABLE novaid_webauthn_registration_challenges (
 challenge_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities, purpose text NOT NULL,
 challenge_hash text NOT NULL, rp_id text NOT NULL, origin text NOT NULL,
 created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL, consumed_at timestamptz,
 status text NOT NULL CHECK(status IN ('PENDING','CONSUMED','EXPIRED','CANCELLED','SUPERSEDED','ATTEMPTS_EXCEEDED')),
 attempt_count integer NOT NULL DEFAULT 0, maximum_attempts integer NOT NULL,
 correlation_id uuid NOT NULL, request_id uuid NOT NULL, CHECK(expires_at>created_at));
CREATE INDEX ix_novaid_webauthn_registration_challenge
ON novaid_webauthn_registration_challenges(tenant_id,identity_id,status,expires_at);

CREATE TABLE novaid_webauthn_authentication_challenges (
 challenge_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid REFERENCES novaid_identities, session_id uuid REFERENCES novaid_authentication_sessions,
 purpose text NOT NULL, challenge_hash text NOT NULL, rp_id text NOT NULL, origin text NOT NULL,
 created_at timestamptz NOT NULL, expires_at timestamptz NOT NULL, consumed_at timestamptz,
 status text NOT NULL CHECK(status IN ('PENDING','CONSUMED','EXPIRED','CANCELLED','SUPERSEDED','ATTEMPTS_EXCEEDED')),
 attempt_count integer NOT NULL DEFAULT 0, maximum_attempts integer NOT NULL,
 correlation_id uuid NOT NULL, request_id uuid NOT NULL, CHECK(expires_at>created_at));
CREATE INDEX ix_novaid_webauthn_authentication_challenge
ON novaid_webauthn_authentication_challenges(tenant_id,identity_id,status,expires_at);

CREATE TABLE novaid_authenticators (
 authenticator_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 aaguid text NOT NULL, friendly_name text, status text NOT NULL,
 created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL, version integer NOT NULL DEFAULT 1);

CREATE TABLE novaid_webauthn_credentials (
 credential_id text PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities, membership_id uuid REFERENCES novaid_tenant_memberships,
 authenticator_id uuid REFERENCES novaid_authenticators, user_handle bytea NOT NULL,
 public_key_cose bytea NOT NULL, public_key_algorithm integer NOT NULL CHECK(public_key_algorithm IN (-7,-8,-257)),
 sign_count bigint NOT NULL DEFAULT 0 CHECK(sign_count>=0), aaguid text NOT NULL,
 attestation_format text NOT NULL, attestation_type text NOT NULL, transports jsonb NOT NULL DEFAULT '[]'::jsonb,
 backup_eligible boolean NOT NULL DEFAULT false, backup_state boolean NOT NULL DEFAULT false,
 discoverable boolean NOT NULL DEFAULT false, resident_key boolean NOT NULL DEFAULT false,
 user_verification boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL,
 last_used_at timestamptz, last_verified_at timestamptz,
 status text NOT NULL CHECK(status IN ('PENDING','ACTIVE','SUSPENDED','REVOKED','COMPROMISED','REPLACED','DELETED')),
 version integer NOT NULL DEFAULT 1, friendly_name text, device_reference text, provider_reference text,
 UNIQUE(tenant_id,user_handle,credential_id));
CREATE INDEX ix_novaid_webauthn_credential_owner
ON novaid_webauthn_credentials(tenant_id,identity_id,status,created_at);
CREATE INDEX ix_novaid_webauthn_credential_aaguid
ON novaid_webauthn_credentials(aaguid,last_used_at);

CREATE TABLE novaid_authenticator_bindings (
 binding_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 identity_id uuid NOT NULL REFERENCES novaid_identities,
 authenticator_id uuid NOT NULL REFERENCES novaid_authenticators,
 status text NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL,
 UNIQUE(tenant_id,identity_id,authenticator_id));
CREATE TABLE novaid_attestation_records (
 attestation_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 credential_id text NOT NULL REFERENCES novaid_webauthn_credentials,
 format text NOT NULL, attestation_type text NOT NULL, trust_path_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 verified_at timestamptz NOT NULL);
CREATE TABLE novaid_authenticator_status_history (
 transition_id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES novaid_tenants,
 credential_id text NOT NULL REFERENCES novaid_webauthn_credentials,
 previous_status text NOT NULL, new_status text NOT NULL, reason_code text NOT NULL,
 occurred_at timestamptz NOT NULL, actor_identity_id uuid NOT NULL);

INSERT INTO novaid_schema_migrations(revision) VALUES ('0004_novaid_webauthn.sql');
