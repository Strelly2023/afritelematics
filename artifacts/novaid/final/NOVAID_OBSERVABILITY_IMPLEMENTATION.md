# NovaID observability implementation

NovaID now has dependency-free counters with an explicit low-cardinality label allowlist and named in-process spans around register, verify, authenticate, MFA issue/verify, and refresh operations. Tests prove identity labels are rejected and recorded spans contain no password material. Metrics export, a production tracer provider, remaining required operation spans, and collector/backend verification remain incomplete.
