CREATE TABLE IF NOT EXISTS novaid_audit_replay_requests (
 replay_request_id uuid PRIMARY KEY,
 tenant_id uuid NOT NULL,
 organization_id uuid NOT NULL,
 environment_id text NOT NULL DEFAULT '',
 requested_by uuid NOT NULL,
 approved_by uuid,
 executed_by uuid,
 event_type_filters jsonb NOT NULL DEFAULT '[]'::jsonb,
 aggregate_filters jsonb NOT NULL DEFAULT '{}'::jsonb,
 subject_filters jsonb NOT NULL DEFAULT '{}'::jsonb,
 start_time timestamptz,
 end_time timestamptz,
 source_checkpoint text,
 target_checkpoint text,
 replay_mode text NOT NULL,
 dry_run boolean NOT NULL DEFAULT true,
 reason text NOT NULL,
 risk_level text NOT NULL,
 status text NOT NULL,
 maximum_events integer NOT NULL DEFAULT 100,
 created_at timestamptz NOT NULL DEFAULT NOW(),
 approved_at timestamptz,
 started_at timestamptz,
 completed_at timestamptz,
 cancelled_at timestamptz,
 evidence_id uuid,
 correlation_id text NOT NULL DEFAULT '',
 request_id text NOT NULL DEFAULT '',
 CHECK (status IN (
   'draft','requested','policy_evaluated','approval_pending','approved','executing',
   'verifying','completed','rejected','cancelled','failed','verification_failed','expired'
 )),
 CHECK (replay_mode IN (
   'inspect_only','dry_run','reprocess_consumer','rebuild_projection','republish_transport'
 )),
 CHECK (maximum_events > 0)
);

CREATE INDEX IF NOT EXISTS ix_novaid_audit_replay_requests_tenant_status
 ON novaid_audit_replay_requests (tenant_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS novaid_audit_replay_approvals (
 approval_id uuid PRIMARY KEY,
 replay_request_id uuid NOT NULL REFERENCES novaid_audit_replay_requests (replay_request_id) ON DELETE CASCADE,
 tenant_id uuid NOT NULL,
 organization_id uuid NOT NULL,
 approver_id uuid NOT NULL,
 decision text NOT NULL,
 reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT NOW(),
 UNIQUE (replay_request_id, approver_id, decision)
);

CREATE TABLE IF NOT EXISTS novaid_audit_replay_event_results (
 result_id uuid PRIMARY KEY,
 replay_request_id uuid NOT NULL REFERENCES novaid_audit_replay_requests (replay_request_id) ON DELETE CASCADE,
 tenant_id uuid NOT NULL,
 organization_id uuid NOT NULL,
 event_id uuid NOT NULL,
 event_type text NOT NULL,
 decision text NOT NULL,
 reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT NOW(),
 UNIQUE (replay_request_id, event_id, decision)
);

CREATE INDEX IF NOT EXISTS ix_novaid_audit_replay_results_request
 ON novaid_audit_replay_event_results (replay_request_id, decision, created_at DESC);

INSERT INTO novaid_schema_migrations(revision)
VALUES ('0008_novaid_governed_audit_replay.sql') ON CONFLICT(revision) DO NOTHING;
