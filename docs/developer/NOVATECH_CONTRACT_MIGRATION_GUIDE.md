# NovaTech Contract Migration Guide

Before upgrading:

1. Retrieve the server version vector.
2. Compare the compatibility matrix.
3. Regenerate SDK contracts.
4. Validate representative request, response, event, trust, and replay payloads.
5. Run consumer contract tests.
6. Deploy to integration, then staging.
7. Verify SLOs, replay equivalence, tenant isolation, and rollback.
8. Promote through governed canary stages.

Major contract changes require an accepted ADR, migration tooling, consumer
inventory, deprecation period, and evidence that old and new replay semantics
are intentionally compatible or explicitly isolated.
