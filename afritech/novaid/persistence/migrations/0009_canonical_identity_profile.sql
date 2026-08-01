ALTER TABLE novaid_identities
    ADD COLUMN IF NOT EXISTS identity_type text NOT NULL DEFAULT 'PERSON',
    ADD COLUMN IF NOT EXISTS legal_name jsonb,
    ADD COLUMN IF NOT EXISTS preferred_name text,
    ADD COLUMN IF NOT EXISTS alternative_names jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS contact_points jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS identifiers jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS verification_status text NOT NULL DEFAULT 'UNVERIFIED',
    ADD COLUMN IF NOT EXISTS assurance_level text NOT NULL DEFAULT 'NID-AL0',
    ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_novaid_identity_type'
          AND conrelid = 'novaid_identities'::regclass
    ) THEN
        ALTER TABLE novaid_identities
            ADD CONSTRAINT ck_novaid_identity_type
            CHECK (
                identity_type IN (
                    'PERSON',
                    'ORGANISATION',
                    'BUSINESS',
                    'GOVERNMENT_ENTITY',
                    'SERVICE_ACCOUNT',
                    'DEPENDENT'
                )
            );
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_novaid_verification_status'
          AND conrelid = 'novaid_identities'::regclass
    ) THEN
        ALTER TABLE novaid_identities
            ADD CONSTRAINT ck_novaid_verification_status
            CHECK (
                verification_status IN (
                    'UNVERIFIED',
                    'PENDING',
                    'IN_PROGRESS',
                    'MANUAL_REVIEW',
                    'VERIFIED',
                    'REJECTED',
                    'EXPIRED'
                )
            );
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_novaid_assurance_level'
          AND conrelid = 'novaid_identities'::regclass
    ) THEN
        ALTER TABLE novaid_identities
            ADD CONSTRAINT ck_novaid_assurance_level
            CHECK (
                assurance_level IN (
                    'NID-AL0',
                    'NID-AL1',
                    'NID-AL2',
                    'NID-AL3',
                    'NID-AL4'
                )
            );
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_novaid_identity_type
    ON novaid_identities(tenant_id, identity_type);

CREATE INDEX IF NOT EXISTS ix_novaid_verification_status
    ON novaid_identities(tenant_id, verification_status);

CREATE INDEX IF NOT EXISTS ix_novaid_assurance_level
    ON novaid_identities(tenant_id, assurance_level);

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0009_canonical_identity_profile.sql')
ON CONFLICT(revision) DO NOTHING;
