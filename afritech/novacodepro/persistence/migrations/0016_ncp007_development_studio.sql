-- NovaCodePro NCP-007 Development Studio migration contract.
-- The runtime persists governed development records in the generic NovaCodePro repository layer.
-- This migration documents the authoritative schema expectation for the phase and the required
-- relational controls for downstream production stores.

CREATE TABLE IF NOT EXISTS development_workspace (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  workspace_id TEXT,
  project_id TEXT,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  repository_id TEXT NOT NULL DEFAULT '',
  default_branch TEXT NOT NULL DEFAULT 'main',
  active_branch TEXT NOT NULL DEFAULT 'main',
  environment_profile_id TEXT NOT NULL DEFAULT '',
  architecture_baseline_id TEXT NOT NULL DEFAULT '',
  design_baseline_id TEXT NOT NULL DEFAULT '',
  requirement_baseline_id TEXT NOT NULL DEFAULT '',
  coding_standard_profile_id TEXT NOT NULL DEFAULT '',
  security_profile_id TEXT NOT NULL DEFAULT '',
  policy_profile_id TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'DRAFT',
  version INTEGER NOT NULL DEFAULT 1,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  causation_id TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS repository_connection (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  project_id TEXT,
  provider TEXT NOT NULL,
  repository_name TEXT NOT NULL,
  repository_url TEXT NOT NULL,
  repository_external_id TEXT NOT NULL DEFAULT '',
  default_branch TEXT NOT NULL DEFAULT 'main',
  local_path_reference TEXT NOT NULL DEFAULT '',
  credential_reference TEXT NOT NULL DEFAULT '',
  connection_status TEXT NOT NULL DEFAULT 'PENDING',
  last_verified_at TEXT NOT NULL DEFAULT '',
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS development_session (
  id TEXT PRIMARY KEY,
  development_workspace_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  branch_name TEXT NOT NULL,
  base_revision TEXT NOT NULL,
  current_revision TEXT NOT NULL,
  objective TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'PLANNING',
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL DEFAULT '',
  correlation_id TEXT NOT NULL,
  trace_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS development_task (
  id TEXT PRIMARY KEY,
  development_session_id TEXT NOT NULL,
  requirement_id TEXT NOT NULL DEFAULT '',
  architecture_element_id TEXT NOT NULL DEFAULT '',
  design_artifact_id TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  acceptance_criteria TEXT NOT NULL DEFAULT '[]',
  task_type TEXT NOT NULL,
  risk_level TEXT NOT NULL DEFAULT 'LOW',
  status TEXT NOT NULL DEFAULT 'DRAFT',
  assigned_actor_id TEXT NOT NULL DEFAULT '',
  assigned_agent_id TEXT NOT NULL DEFAULT '',
  sequence INTEGER NOT NULL DEFAULT 0,
  dependencies TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS code_generation_request (
  id TEXT PRIMARY KEY,
  development_session_id TEXT NOT NULL,
  development_task_id TEXT NOT NULL,
  requester_id TEXT NOT NULL,
  instruction TEXT NOT NULL,
  context_snapshot_id TEXT NOT NULL DEFAULT '',
  target_files TEXT NOT NULL DEFAULT '[]',
  excluded_files TEXT NOT NULL DEFAULT '[]',
  generation_mode TEXT NOT NULL DEFAULT 'MODIFY',
  model_provider TEXT NOT NULL DEFAULT '',
  model_name TEXT NOT NULL DEFAULT '',
  policy_profile_id TEXT NOT NULL DEFAULT '',
  risk_level TEXT NOT NULL DEFAULT 'LOW',
  status TEXT NOT NULL DEFAULT 'GENERATED',
  requested_at TEXT NOT NULL,
  completed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS generated_change_set (
  id TEXT PRIMARY KEY,
  code_generation_request_id TEXT NOT NULL,
  repository_id TEXT NOT NULL,
  base_revision TEXT NOT NULL,
  proposed_revision TEXT NOT NULL,
  summary TEXT NOT NULL,
  rationale TEXT NOT NULL,
  risk_level TEXT NOT NULL DEFAULT 'LOW',
  status TEXT NOT NULL DEFAULT 'GENERATED',
  files_added_count INTEGER NOT NULL DEFAULT 0,
  files_modified_count INTEGER NOT NULL DEFAULT 0,
  files_deleted_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_change (
  id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  path TEXT NOT NULL,
  operation TEXT NOT NULL,
  previous_hash TEXT NOT NULL DEFAULT '',
  proposed_hash TEXT NOT NULL DEFAULT '',
  previous_content_reference TEXT NOT NULL DEFAULT '',
  proposed_content_reference TEXT NOT NULL DEFAULT '',
  diff_reference TEXT NOT NULL DEFAULT '',
  language TEXT NOT NULL DEFAULT 'text',
  generated_by TEXT NOT NULL,
  risk_flags TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_run (
  id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  validation_type TEXT NOT NULL,
  command TEXT NOT NULL DEFAULT '[]',
  execution_environment_id TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'NOT_STARTED',
  exit_code INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  completed_at TEXT NOT NULL DEFAULT '',
  duration_ms INTEGER NOT NULL DEFAULT 0,
  output_reference TEXT NOT NULL DEFAULT '',
  error_reference TEXT NOT NULL DEFAULT '',
  evidence_id TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS code_review (
  id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  reviewer_id TEXT NOT NULL DEFAULT '',
  reviewer_type TEXT NOT NULL DEFAULT 'HUMAN',
  status TEXT NOT NULL DEFAULT 'PENDING',
  summary TEXT NOT NULL DEFAULT '',
  risk_assessment TEXT NOT NULL DEFAULT 'LOW',
  reviewed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS review_comment (
  id TEXT PRIMARY KEY,
  code_review_id TEXT NOT NULL,
  file_path TEXT NOT NULL DEFAULT '',
  line_start INTEGER NOT NULL DEFAULT 0,
  line_end INTEGER NOT NULL DEFAULT 0,
  comment_type TEXT NOT NULL DEFAULT 'GENERAL',
  severity TEXT NOT NULL DEFAULT 'LOW',
  body TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'OPEN',
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_by TEXT NOT NULL DEFAULT '',
  resolved_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS development_approval (
  id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  approval_type TEXT NOT NULL,
  approver_id TEXT NOT NULL,
  decision TEXT NOT NULL DEFAULT 'PENDING',
  conditions TEXT NOT NULL DEFAULT '[]',
  reason TEXT NOT NULL DEFAULT '',
  policy_evaluation_id TEXT NOT NULL DEFAULT '',
  decided_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS commit_proposal (
  id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  branch_name TEXT NOT NULL,
  commit_message TEXT NOT NULL,
  author_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  resulting_commit_hash TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  executed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS development_evidence_package (
  id TEXT PRIMARY KEY,
  development_session_id TEXT NOT NULL,
  change_set_id TEXT NOT NULL,
  requirement_trace_reference TEXT NOT NULL DEFAULT '',
  architecture_trace_reference TEXT NOT NULL DEFAULT '',
  design_trace_reference TEXT NOT NULL DEFAULT '',
  policy_results_reference TEXT NOT NULL DEFAULT '',
  validation_results_reference TEXT NOT NULL DEFAULT '',
  review_reference TEXT NOT NULL DEFAULT '',
  approval_reference TEXT NOT NULL DEFAULT '',
  repository_diff_reference TEXT NOT NULL DEFAULT '',
  commit_reference TEXT NOT NULL DEFAULT '',
  build_reference TEXT NOT NULL DEFAULT '',
  integrity_hash TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS context_snapshot (
  id TEXT PRIMARY KEY,
  development_session_id TEXT NOT NULL,
  development_task_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS context_snapshot_item (
  id TEXT PRIMARY KEY,
  context_snapshot_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_version TEXT NOT NULL DEFAULT '',
  content_hash TEXT NOT NULL DEFAULT '',
  included_reason TEXT NOT NULL DEFAULT '',
  authorization_decision TEXT NOT NULL DEFAULT '',
  retrieved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS development_event (
  id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  workspace_id TEXT NOT NULL DEFAULT '',
  project_id TEXT NOT NULL DEFAULT '',
  request_id TEXT NOT NULL DEFAULT '',
  actor_id TEXT NOT NULL,
  session_id TEXT NOT NULL DEFAULT '',
  correlation_id TEXT NOT NULL,
  causation_id TEXT NOT NULL DEFAULT '',
  previous_state TEXT NOT NULL DEFAULT '',
  new_state TEXT NOT NULL DEFAULT '',
  result TEXT NOT NULL DEFAULT 'SUCCESS',
  error_code TEXT NOT NULL DEFAULT '',
  evidence_reference TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dev_workspace_tenant_org ON development_workspace(tenant_id, organization_id, workspace_id, project_id);
CREATE INDEX IF NOT EXISTS idx_dev_workspace_status ON development_workspace(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_session_workspace ON development_session(development_workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_task_session ON development_task(development_session_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_generation_session ON code_generation_request(development_session_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_change_set_request ON generated_change_set(code_generation_request_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_file_change_change_set ON file_change(change_set_id, path);
CREATE INDEX IF NOT EXISTS idx_dev_validation_change_set ON validation_run(change_set_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_review_change_set ON code_review(change_set_id, status);
CREATE INDEX IF NOT EXISTS idx_dev_approval_change_set ON development_approval(change_set_id, decision);
CREATE INDEX IF NOT EXISTS idx_dev_evidence_session ON development_evidence_package(development_session_id, change_set_id);
CREATE INDEX IF NOT EXISTS idx_dev_context_snapshot_session ON context_snapshot(development_session_id, development_task_id);
CREATE INDEX IF NOT EXISTS idx_dev_event_type ON development_event(event_type, tenant_id);
