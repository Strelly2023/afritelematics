# NovaTech Platform Release Policy

Platform, contract, schema, API, replay, evidence, and signature versions evolve
independently and travel together in a version vector.

Semantic versioning applies. Major versions may break compatibility and require
migration. Minor versions are backward-compatible additions. Patch versions
preserve contract behavior. Stable and LTS APIs cannot remove or reinterpret
fields without a major version.

Lifecycle is `DRAFT -> EXPERIMENTAL -> STABLE -> LTS -> DEPRECATED -> RETIRED`.
Promotion requires contract tests, security review, observability, rollback,
compatibility evidence, documentation, and an owner. Deprecation requires
inventory of consumers, published replacement, migration tooling, notice
period, telemetry, and retirement approval. Emergency security retirement must
record rationale and compensating migration support.
