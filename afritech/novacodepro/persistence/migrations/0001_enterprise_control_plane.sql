CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS identity_context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    subject_id TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    canonical_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    authority_grants JSONB NOT NULL DEFAULT '[]'::jsonb,
    authentication_strength TEXT NOT NULL,
    device_trust INTEGER NOT NULL,
    session_risk INTEGER NOT NULL,
    jurisdiction TEXT NOT NULL,
    region TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS enterprise_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_key TEXT NOT NULL,
    object_type TEXT NOT NULL,
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    owner_id TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    classification TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    region TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    object_version BIGINT NOT NULL DEFAULT 1,
    correlation_id TEXT NOT NULL,
    policy_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (tenant_id, object_type, object_key)
);

CREATE TABLE IF NOT EXISTS enterprise_object_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID NOT NULL REFERENCES enterprise_objects(id),
    tenant_id UUID NOT NULL,
    object_version BIGINT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (object_id, object_version)
);

CREATE TABLE IF NOT EXISTS enterprise_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    assertion_type TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    criticality TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until TIMESTAMPTZ,
    source_system TEXT NOT NULL,
    review_status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, source_id, target_id, relationship_type, valid_from)
);

CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_key TEXT NOT NULL,
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL,
    temporal_workflow_id TEXT NOT NULL,
    temporal_run_id TEXT,
    idempotency_key TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS workflow_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_executions(id),
    tenant_id UUID NOT NULL,
    stage_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS workflow_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_executions(id),
    tenant_id UUID NOT NULL,
    command_type TEXT NOT NULL,
    command_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_compensations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_executions(id),
    tenant_id UUID NOT NULL,
    compensation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policy_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    policy_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    risk_score NUMERIC(10,2) NOT NULL,
    classification TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    subject_hash TEXT NOT NULL,
    plan_version BIGINT NOT NULL,
    requester_id TEXT NOT NULL,
    required_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_quorum INTEGER NOT NULL DEFAULT 1,
    conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    expires_at TIMESTAMPTZ,
    reusable BOOLEAN NOT NULL DEFAULT false,
    status TEXT NOT NULL,
    consumed_by_execution TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approval_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id UUID NOT NULL REFERENCES approval_requests(id),
    tenant_id UUID NOT NULL,
    subject_id TEXT NOT NULL,
    role TEXT NOT NULL,
    decision TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    agent_id TEXT NOT NULL,
    workflow_id UUID,
    status TEXT NOT NULL,
    credential_ref TEXT,
    approval_id UUID,
    expires_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS tool_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    workspace_id UUID,
    task_id UUID NOT NULL REFERENCES agent_tasks(id),
    tool_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    allowed_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    resource_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    approval_id UUID,
    single_use BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS digital_twins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_key TEXT NOT NULL,
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    represented_entity_id TEXT NOT NULL,
    twin_type TEXT NOT NULL,
    status TEXT NOT NULL,
    classification TEXT NOT NULL,
    region TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, twin_key)
);

CREATE TABLE IF NOT EXISTS digital_twin_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_id UUID NOT NULL REFERENCES digital_twins(id),
    tenant_id UUID NOT NULL,
    state_type TEXT NOT NULL,
    state_version BIGINT NOT NULL,
    status TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until TIMESTAMPTZ,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (twin_id, state_type, state_version)
);

CREATE TABLE IF NOT EXISTS digital_twin_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    twin_id UUID,
    source_identity TEXT NOT NULL,
    source_type TEXT NOT NULL,
    signal TEXT NOT NULL,
    value JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    quality TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    classification TEXT NOT NULL,
    region TEXT NOT NULL,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    knowledge_type TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    authority_level INTEGER NOT NULL,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_by_actor_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    classification TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS knowledge_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    knowledge_id UUID NOT NULL REFERENCES knowledge_items(id),
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    conflicts_unresolved BOOLEAN NOT NULL DEFAULT false,
    approved_authority_level INTEGER,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    evidence_key TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    signature_algorithm TEXT NOT NULL,
    signing_key_id TEXT NOT NULL,
    object_uri TEXT NOT NULL,
    workflow_id UUID,
    approval_id UUID,
    twin_id UUID,
    knowledge_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS event_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    event_payload JSONB NOT NULL,
    payload_hash TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    publish_attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS event_inbox (
    consumer_name TEXT NOT NULL,
    event_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload_hash TEXT NOT NULL,
    PRIMARY KEY (consumer_name, event_id)
);

CREATE TABLE IF NOT EXISTS projection_offsets (
    projection_name TEXT NOT NULL,
    tenant_id UUID NOT NULL,
    last_event_id UUID,
    projection_version BIGINT NOT NULL DEFAULT 0,
    as_of TIMESTAMPTZ NOT NULL DEFAULT now(),
    state_hash TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (projection_name, tenant_id)
);

CREATE TABLE IF NOT EXISTS continuous_assurance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    control_id TEXT NOT NULL,
    assurance_state TEXT NOT NULL,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    independent_verifier_id TEXT,
    expires_at TIMESTAMPTZ,
    risk_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

