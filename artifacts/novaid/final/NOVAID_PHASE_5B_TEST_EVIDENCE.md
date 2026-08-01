# NovaID Phase 5B test evidence

- Password lifecycle: 2 passed.
- Temporary lockout: 1 passed.
- Session administration/expiry/compromise: 2 passed.
- Final combined suite with PostgreSQL and Redis: 37 passed, 0 failed, 0 skipped, one warning.
- Full NovaID Ruff: PASS.
- Compileall: PASS.
- `git diff --check`: PASS.
- Infrastructure: PostgreSQL 14.20, Redis 8.4.0, psycopg 3.3.4, Python 3.11.8.
