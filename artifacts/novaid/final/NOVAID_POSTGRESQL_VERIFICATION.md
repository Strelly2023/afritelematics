# PostgreSQL verification

Result: **BLOCKED / NOT EXECUTED**. No isolated NovaID PostgreSQL service was configured in the environment. The migration exists, but row locking, JSONB, constraints, indexes, rollback and concurrency were not executed on PostgreSQL and are not certified.
