CREATE TABLE IF NOT EXISTS approval_workflows (id TEXT PRIMARY KEY, release_id TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS approval_steps (id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS approval_decisions (id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, actor_id TEXT NOT NULL, role TEXT NOT NULL, decision TEXT NOT NULL, signature TEXT NOT NULL, payload JSONB NOT NULL);
