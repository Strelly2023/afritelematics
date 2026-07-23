# NCP-009 AI Auto-Generator API

Base path: `/api/v1/ai-auto-generator`

Implemented routes:

- `POST /executions`
- `GET /executions`
- `GET /executions/{execution_id}`
- `POST /executions/{execution_id}/approvals`
- `POST /executions/{execution_id}/retry`
- `POST /executions/{execution_id}/pause`
- `POST /executions/{execution_id}/resume`
- `POST /executions/{execution_id}/cancel`
- `POST /executions/{execution_id}/artifacts/{artifact_id}/regenerate`
- `GET /projects/{project_id}/traceability`
- `GET /projects/{project_id}/evidence`

Behavior:

- execution creation is workspace-scoped and idempotency-aware
- the service emits deterministic stage artifacts for the full 11-stage lifecycle
- human approval is required for stage promotion
- evidence and traceability are stored per project and per execution
- cross-tenant access is rejected server-side

Stage chain:

1. AI Strategy Service
2. AI Planning Service
3. AI Requirements Service
4. AI UX and Design Service
5. AI Architecture Service
6. AI Applications Service
7. AI Intelligent Identity Assurance Service
8. AI Identity Operations Service
9. AI Portals Service
10. AI Analytics Service
11. AI Production Release Service
