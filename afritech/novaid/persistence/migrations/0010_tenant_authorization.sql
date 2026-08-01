ALTER TABLE novaid_tenants
    ADD COLUMN IF NOT EXISTS tenant_type TEXT NOT NULL DEFAULT 'ORGANISATION',
    ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'STANDARD',
    ADD COLUMN IF NOT EXISTS legal_entity JSONB,
    ADD COLUMN IF NOT EXISTS brand JSONB,
    ADD COLUMN IF NOT EXISTS settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS security_policy JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE novaid_tenant_memberships
    ADD COLUMN IF NOT EXISTS roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS direct_permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS valid_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT ck_novaid_membership_status
        CHECK (status IN ('INVITED','ACTIVE','SUSPENDED','REVOKED','EXPIRED')),
    ADD CONSTRAINT ck_novaid_membership_validity
        CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from);

CREATE TABLE IF NOT EXISTS novaid_permissions(
    permission_id TEXT PRIMARY KEY,
    tenant_id UUID REFERENCES novaid_tenants(tenant_id),
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    effect TEXT NOT NULL CHECK (effect IN ('ALLOW','DENY')),
    resource_owner_only BOOLEAN NOT NULL DEFAULT FALSE,
    require_trusted_device BOOLEAN NOT NULL DEFAULT FALSE,
    minimum_assurance_level TEXT NOT NULL DEFAULT 'NID-AL0',
    minimum_authentication_strength TEXT NOT NULL DEFAULT 'PASSWORD',
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE NULLS NOT DISTINCT(tenant_id,resource,action,effect)
);

CREATE TABLE IF NOT EXISTS novaid_roles(
    role_id TEXT PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES novaid_tenants(tenant_id),
    name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    UNIQUE(tenant_id,name)
);

CREATE TABLE IF NOT EXISTS novaid_role_permissions(
    tenant_id UUID NOT NULL REFERENCES novaid_tenants(tenant_id),
    role_id TEXT NOT NULL REFERENCES novaid_roles(role_id),
    permission_id TEXT NOT NULL REFERENCES novaid_permissions(permission_id),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY(tenant_id,role_id,permission_id)
);

CREATE TABLE IF NOT EXISTS novaid_membership_roles(
    tenant_id UUID NOT NULL REFERENCES novaid_tenants(tenant_id),
    membership_id UUID NOT NULL REFERENCES novaid_tenant_memberships(membership_id),
    role_id TEXT NOT NULL REFERENCES novaid_roles(role_id),
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY(tenant_id,membership_id,role_id),
    CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
);

CREATE TABLE IF NOT EXISTS novaid_authorization_policy_versions(
    tenant_id UUID NOT NULL REFERENCES novaid_tenants(tenant_id),
    policy_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','ACTIVE','RETIRED')),
    policy_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    activated_at TIMESTAMPTZ,
    created_by TEXT NOT NULL,
    PRIMARY KEY(tenant_id,policy_version)
);

CREATE INDEX IF NOT EXISTS ix_novaid_membership_roles_effective
    ON novaid_membership_roles(tenant_id,membership_id,valid_until);
CREATE INDEX IF NOT EXISTS ix_novaid_role_permissions_tenant
    ON novaid_role_permissions(tenant_id,role_id);

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0010_tenant_authorization.sql')
ON CONFLICT (revision) DO NOTHING;
