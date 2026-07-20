# GA gate catalog

This catalog defines the governance language used by the release-baseline tooling.

Each gate result is binary at the criterion level and can only be one of:

- PASS
- FAIL
- BLOCKED
- NOT_RUN

Product gate summaries may classify a product as blocked, partial, or ready only after all mandatory criteria are evaluated against commit-bound evidence.

The release-baseline tooling intentionally treats missing approvals, missing evidence, dirty worktrees, and cross-commit contamination as blocking conditions rather than as passing evidence.
