DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'identity_context_snapshots',
        'enterprise_objects',
        'enterprise_object_versions',
        'enterprise_relationships',
        'workflow_executions',
        'workflow_stages',
        'workflow_commands',
        'workflow_compensations',
        'policy_decisions',
        'risk_assessments',
        'approval_requests',
        'approval_votes',
        'agent_tasks',
        'tool_authorizations',
        'digital_twins',
        'digital_twin_states',
        'digital_twin_observations',
        'knowledge_items',
        'knowledge_reviews',
        'evidence_metadata',
        'event_outbox',
        'event_inbox',
        'projection_offsets',
        'continuous_assurance_records'
    ]
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format(
            'DROP POLICY IF EXISTS %I ON %I',
            table_name || '_tenant_isolation',
            table_name
        );
        EXECUTE format(
            'CREATE POLICY %I ON %I USING (tenant_id::text = current_setting(''app.tenant_id'', true)) WITH CHECK (tenant_id::text = current_setting(''app.tenant_id'', true))',
            table_name || '_tenant_isolation',
            table_name
        );
    END LOOP;
END $$;

CREATE OR REPLACE FUNCTION novacodepro_apply_security_context(
    p_tenant_id text,
    p_organization_id text,
    p_workspace_id text,
    p_subject_id text
) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.tenant_id', p_tenant_id, true);
    PERFORM set_config('app.organization_id', p_organization_id, true);
    PERFORM set_config('app.workspace_id', p_workspace_id, true);
    PERFORM set_config('app.subject_id', p_subject_id, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

