# NovaID dependency wiring

`build_default_durable_router` composes the unit of work, lockout, durable authentication, password, session, access-token, and revocation services. Development defaults to an explicit SQLite file. Production refuses a non-PostgreSQL URL, but PostgreSQL application composition intentionally fails closed because the service-level adapter is unfinished. Redis revocation is selected when configured; production refuses process-local revocation.
