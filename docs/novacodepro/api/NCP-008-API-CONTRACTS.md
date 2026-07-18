# NCP-008 API Contracts

Base path: `/api/v1/operations`

All endpoints require authentication and enforce tenant scope.

Implemented groups include:

- workspaces
- environments
- services
- deployments
- alerts
- incidents
- actions
- SLOs
- recovery plans
- post-incident reviews
- health
- telemetry
- on-call and escalation
- change management
- rollback / backup / restore / failover / DR / capacity / maintenance / runbooks / commands / postmortems / corrective actions / baselines

Response shapes are typed JSON objects and collection responses use `{items, count}`-style envelopes.

Structured error format:

```json
{
  "error": {
    "code": "OPERATIONS_ACTION_APPROVAL_REQUIRED",
    "message": "This production operation requires approval.",
    "details": {},
    "request_id": "...",
    "trace_id": "..."
  }
}
```

Protected routes return JSON `401` rather than HTML.
