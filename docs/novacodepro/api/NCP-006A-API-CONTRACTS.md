# NCP-006A API Contracts

Base path: `/v1/novacodepro/architecture`

Implemented groups:

- workspaces
- models
- components
- interfaces
- data
- security
- deployments
- reviews
- approvals
- baselines
- validation
- fitness
- diagrams
- impact
- relationships
- traceability

All routes enforce tenant-aware session context and architecture permissions. Model-scoped operations resolve against the model workspace before executing.
