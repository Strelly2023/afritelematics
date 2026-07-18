# NCP-004 AI API Contracts

Base path: `/v1/novacodepro/ai`

Implemented routes:

- `POST /executions`
- `GET /executions`
- `GET /executions/{execution_id}`
- `POST /executions/{execution_id}/analyse`
- `GET /executions/{execution_id}/clarifications`
- `POST /executions/{execution_id}/clarifications/{clarification_id}/answer`
- `POST /executions/{execution_id}/clarifications/complete`
- `POST /executions/{execution_id}/generate-requirements`
- `POST /executions/{execution_id}/generate-plan`
- `GET /executions/{execution_id}/plan`
- `POST /executions/{execution_id}/plan/validate`
- `POST /executions/{execution_id}/request-approval`
- `GET /approvals`
- `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/approve`
- `POST /approvals/{approval_id}/reject`
- `POST /approvals/{approval_id}/request-changes`
- `POST /executions/{execution_id}/execute`
- `POST /executions/{execution_id}/verify`
- `POST /executions/{execution_id}/cancel`
- `POST /executions/{execution_id}/pause`
- `POST /executions/{execution_id}/resume`
- `POST /executions/{execution_id}/rollback`
- `GET /executions/{execution_id}/timeline`
- `GET /executions/{execution_id}/evidence`
- `GET /executions/{execution_id}/replay`
- `GET /agents`
- `GET /agents/{agent_id}`
- `POST /agents`
- `PATCH /agents/{agent_id}`
- `POST /agents/{agent_id}/versions`
- `POST /agents/{agent_id}/enable`
- `POST /agents/{agent_id}/disable`
- `GET /tools`
- `GET /tools/{tool_id}`
- `POST /tools/{tool_id}/enable`
- `POST /tools/{tool_id}/disable`
- `GET /notifications`
- `PATCH /notifications/{notification_id}/read`
- `POST /notifications/read-all`

Error shape:

```json
{
  "error": {
    "code": "policy_denied",
    "message": "Denied.",
    "correlationId": "corr-...",
    "retryable": false,
    "details": {}
  }
}
```

Important behavior:

- execution creation requires server-authoritative tenant, workspace, and permissions
- plan generation requires generated requirements and valid agent/tool registry entries
- approval decisions are enforced by role and approval state
- verification is required before completion
