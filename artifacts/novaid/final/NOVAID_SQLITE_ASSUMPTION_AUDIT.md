# NovaID SQLite assumption audit

| Assumption | Callers | PostgreSQL handling | Status |
|---|---|---|---|
| `?` parameters | auth/password/session/token/API | portable connection maps to `%s` | Transitional |
| `INSERT OR REPLACE` | lockout | explicit PostgreSQL `ON CONFLICT` mapping | Transitional |
| `BEGIN IMMEDIATE` | SQLite UOW | pooled PostgreSQL `BEGIN` | Replaced for PostgreSQL |
| string timestamps/UUIDs | all services | normalized portable rows | Replaced for PostgreSQL |
| UUID-to-text MFA join | MFA verification | portable SQL `CAST(... AS TEXT)` | Replaced |
| persistent connection | token/API reads | short pooled read operations | Replaced |
| direct SQL in services | core services | still present | Open gap |
