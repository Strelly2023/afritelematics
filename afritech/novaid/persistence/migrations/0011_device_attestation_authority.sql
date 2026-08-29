-- NovaID migration revision: 0011_device_attestation_authority.sql
-- Target-native C24 schema, semantically rebased from source revision 0022.
CREATE TABLE novaid_device_attestation_challenges (
 challenge_id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL REFERENCES novaid_tenants(tenant_id),
 subject_id uuid NOT NULL,
 device_id text NOT NULL,
 provider text NOT NULL CHECK(provider IN ('PLAY_INTEGRITY','APP_ATTEST')),
 nonce_hash text NOT NULL UNIQUE,
 request_id uuid NOT NULL,
 correlation_id uuid NOT NULL,
 issued_at timestamptz NOT NULL,
 expires_at timestamptz NOT NULL,
 consumed_at timestamptz,
 verified_at timestamptz,
 verification_status text NOT NULL DEFAULT 'UNVERIFIED'
   CHECK(verification_status IN ('UNVERIFIED','VERIFIED','INTEGRITY_FAILED','UNAVAILABLE')),
 verdicts jsonb NOT NULL DEFAULT '[]'::jsonb,
 status text NOT NULL CHECK(status IN ('ISSUED','CONSUMED')),
 CHECK(expires_at > issued_at),
 UNIQUE(tenant_id, request_id)
);
CREATE INDEX idx_novaid_device_attestation_scope
 ON novaid_device_attestation_challenges(tenant_id,subject_id,device_id,status,expires_at);
