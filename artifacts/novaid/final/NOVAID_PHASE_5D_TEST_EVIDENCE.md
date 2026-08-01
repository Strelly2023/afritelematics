# NovaID Phase 5D test evidence

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

- PostgreSQL runtime/pool/outbox: 3 passed, 0 failed, 0 skipped, 1 warning in 5.29s.
- Existing PostgreSQL UOW tests: 2 passed in 19.02s.
- Combined suite: 55 passed, 0 failed, 0 skipped, 12 warnings in 170.67s.
- Python 3.11.8; PostgreSQL 14.20; Redis 8.4.0; psycopg 3.3.4.
- Revisions: `0001_identity_core.sql`, `0002_novaid_runtime.sql`.
- Infrastructure: isolated PostgreSQL port 55432 and Redis port 56379/db 15.
- Race workers/iterations: 1/0. Deadlocks: 0. Serialization failures: 0.
