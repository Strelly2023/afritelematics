# NovaID tenant isolation model

Every scoped repository operation requires a complete `RequestContext`. Queries bind both resource identifier and tenant identifier and return `TENANT_ACCESS_DENIED` without cross-tenant fallback. Updates also bind tenant and expected version. Cross-tenant platform authority is not implemented in this phase, so access fails closed.
