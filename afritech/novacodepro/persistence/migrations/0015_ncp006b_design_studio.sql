-- NovaCodePro NCP-006B Design Studio migration contract.
-- The platform currently persists governed records in the NovaCodePro repository layer,
-- but this migration document captures the authoritative schema expectation for the phase.

CREATE TABLE IF NOT EXISTS design_workspace (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  workspace_id TEXT,
  project_id TEXT,
  request_id TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'DRAFT',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  causation_id TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS experience_brief_version (
  id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  correlation_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS design_token (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workspace_id TEXT,
  project_id TEXT,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  category TEXT NOT NULL,
  level TEXT NOT NULL,
  value TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'DRAFT',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  causation_id TEXT,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS brand (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workspace_id TEXT,
  project_id TEXT,
  name TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'DRAFT',
  attributes TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_design_token_tenant_path ON design_token(tenant_id, path);
CREATE UNIQUE INDEX IF NOT EXISTS idx_design_brand_tenant_name ON brand(tenant_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_design_component_version ON component_definition(tenant_id, name, version);
CREATE UNIQUE INDEX IF NOT EXISTS idx_design_localization_locale_key ON localization_resource(tenant_id, locale, key);
CREATE INDEX IF NOT EXISTS idx_design_traceability_source ON design_traceability_link(tenant_id, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_design_traceability_target ON design_traceability_link(tenant_id, target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_design_baseline_project ON design_baseline(tenant_id, design_project_id, status);
CREATE INDEX IF NOT EXISTS idx_design_validation_result_resource ON design_validation_result(tenant_id, resource_type, resource_id);

-- Representative governed collections used by the service layer:
-- experience_brief, research_study, persona, journey_map, service_blueprint,
-- information_architecture, user_flow, wireframe, screen_design, design_system,
-- design_token, theme, brand, component_definition, interaction_pattern,
-- responsive_specification, content_specification, localization_resource,
-- accessibility_requirement, prototype, design_review, design_approval,
-- design_baseline, design_validation_rule, design_validation_result,
-- design_traceability_link, design_traceability_snapshot, design_coverage,
-- design_evidence_package, design_generation_record, design_import,
-- design_export, design_metric_record, design_handoff, design_impact_analysis,
-- design_drift, design_risk, design_debt_item.
