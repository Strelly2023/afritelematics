# NovaID Phase 5C test evidence

- Command: `NOVAID_TEST_DATABASE_URL='postgresql://novaid_test@localhost:55432/novaid_test?host=/tmp' NOVAID_TEST_REDIS_URL='redis://127.0.0.1:56379/15' .venv-review/bin/python -m pytest -q afritech/tests/novaid/test_novaid_ecosystem.py tests/novaid`
- Exit: 0; 52 passed, 0 failed, 0 skipped, 12 warnings in 28.08s.
- Focused mounted-router and startup suite: 15 passed, 0 failed, 0 skipped, 12 warnings in 44.78s.
- Ruff: exit 0, all NovaID checks passed.
- Runtime: Python 3.11.8, PostgreSQL 14.20, Redis 8.4.0, psycopg 3.3.4; migration `0002_novaid_authentication.sql` (schema revision 2).
- Infrastructure: isolated local PostgreSQL on 55432 and Redis on 56379. Pytest worker count 1. Phase 5C race iterations: 0.
