# PostgreSQL repository model

`PostgresNovaIdUnitOfWork` owns one psycopg transaction and exposes explicit repositories. Tenant-scoped reads bind tenant identifiers. Identity optimistic updates use expected versions. OTP, session, refresh-token and idempotency security lookups use `FOR UPDATE`. Exit commits on success, rolls back on failure, and closes the connection.
