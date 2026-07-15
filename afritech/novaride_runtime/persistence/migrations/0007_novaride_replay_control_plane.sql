CREATE TABLE IF NOT EXISTS novaride_replay_plans (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    workspace_id UUID,
    name TEXT NOT NULL,
    description TEXT,
    scenario_type TEXT NOT NULL,
    source_reference TEXT,
    target_environment TEXT NOT NULL,
    status TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    actions JSONB NOT NULL DEFAULT '[]',
    affected_resources JSONB NOT NULL DEFAULT '[]',
    validation_requirements JSONB NOT NULL DEFAULT '[]',
    rollback_plan JSONB NOT NULL DEFAULT '{}'::jsonb,
    plan_hash TEXT NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    idempotency_key TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ,
    promoted_at TIMESTAMPTZ,
    UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS novaride_replay_results (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    replay_plan_id UUID NOT NULL,
    plan_version BIGINT NOT NULL,
    execution_status TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    result_payload JSONB NOT NULL,
    result_hash TEXT NOT NULL,
    executed_by TEXT NOT NULL,
    validated_by TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_at TIMESTAMPTZ,
    FOREIGN KEY (replay_plan_id)
      REFERENCES novaride_replay_plans(id)
);

CREATE TABLE IF NOT EXISTS novaride_replay_approvals (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    replay_plan_id UUID NOT NULL,
    plan_version BIGINT NOT NULL,
    plan_hash TEXT NOT NULL,
    required_quorum INTEGER NOT NULL,
    status TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    consumed_at TIMESTAMPTZ,
    consumed_by_execution_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (replay_plan_id)
      REFERENCES novaride_replay_plans(id)
);

CREATE TABLE IF NOT EXISTS novaride_replay_approval_votes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    approval_id UUID NOT NULL,
    approver_id TEXT NOT NULL,
    approver_role TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (approval_id)
      REFERENCES novaride_replay_approvals(id),
    UNIQUE (tenant_id, approval_id, approver_id)
);

CREATE TABLE IF NOT EXISTS novaride_replay_transitions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    replay_plan_id UUID NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    version BIGINT NOT NULL,
    actor_id TEXT NOT NULL,
    reason TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS novaride_runtime_idempotency (
    tenant_id UUID NOT NULL,
    operation TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_body JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, operation, idempotency_key)
);

CREATE TABLE IF NOT EXISTS novaride_runtime_audit (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    result TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    payload_hash TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE novaride_replay_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_plans FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_results FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_approvals FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_approval_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_approval_votes FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_replay_transitions FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_runtime_idempotency ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_runtime_idempotency FORCE ROW LEVEL SECURITY;
ALTER TABLE novaride_runtime_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE novaride_runtime_audit FORCE ROW LEVEL SECURITY;

CREATE POLICY novaride_replay_plan_tenant_isolation
ON novaride_replay_plans
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_replay_result_tenant_isolation
ON novaride_replay_results
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_replay_approval_tenant_isolation
ON novaride_replay_approvals
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_replay_vote_tenant_isolation
ON novaride_replay_approval_votes
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_replay_transition_tenant_isolation
ON novaride_replay_transitions
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_runtime_idempotency_tenant_isolation
ON novaride_runtime_idempotency
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY novaride_runtime_audit_tenant_isolation
ON novaride_runtime_audit
USING (tenant_id::text = current_setting('app.tenant_id', true))
WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
