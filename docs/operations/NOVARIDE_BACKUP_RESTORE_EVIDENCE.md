# NovaRide Backup and Restore Evidence

Current state: `PENDING`

The repository includes backup, restore, and backup-restore verification entrypoints. A full PASS requires a live PostgreSQL/Event Store backup, isolated restore, projection replay, state hash comparison, tenant/region isolation checks, and proof that external side effects remain blocked.
