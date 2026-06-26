# NovaTech API Contract Standard

Every API operation MUST declare an owner, purpose, lifecycle state, audience,
tenant boundary, authentication, authorization, request schema, response
schema, error schema, idempotency behavior, rate limit, timeout, evidence,
replay behavior, events, SLO, and version vector.

State-changing requests require an idempotency key and return a governed
envelope containing `data`, `meta`, `trust`, and `links`. `meta` identifies
request, tenant, API version, schema version, and achieved trust level. Errors
use stable machine codes and MUST NOT expose secrets.

Compatibility follows `docs/standards/PLATFORM_RELEASE_POLICY.md`. Stable and
LTS contracts require consumer tests, deprecation notice, migration guidance,
and a defined support window. Unknown fields are rejected on authoritative
commands unless the schema explicitly declares forward-compatible extensions.

OpenAPI descriptions are documentation; the canonical JSON Schemas under
`afritech/platform_contracts/schemas` are validation authority for governed
envelopes.
