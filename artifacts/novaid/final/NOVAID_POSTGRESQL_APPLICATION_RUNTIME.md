# NovaID PostgreSQL application runtime

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

`NOVAID_PERSISTENCE_BACKEND=postgres` creates a bounded psycopg pool, checks connectivity and exact migration revisions, builds a pooled unit of work, and mounts the same authentication services used by SQLite. Commit, rollback, exception return, pool exhaustion, tenant isolation, row locks, and optimistic concurrency are tested. Direct service SQL remains a known architectural gap.
