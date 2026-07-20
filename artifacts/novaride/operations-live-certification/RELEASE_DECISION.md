# NovaRide Operations live certification decision

Decision: OPERATIONS_CERTIFIED_LOCAL_ONLY

Local status:
- Canonical operations routes are mounted under `/api/v1/novaride/operations`.
- CORS allows the approved browser origin and rejects an unapproved origin.
- Bootstrap is available in the test runtime.
- Positive browser workflows, degraded workflows, accessibility, visual regression, backend tests, and runtime tests passed.

Blocked externally:
- Live deployed verification was not executed in this turn.

This decision only covers the repository-controlled local certification surface.
