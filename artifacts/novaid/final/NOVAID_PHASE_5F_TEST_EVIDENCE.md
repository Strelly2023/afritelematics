# NovaID Phase 5F test evidence

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

- Combined: 63 passed, 0 failed, 0 skipped, 12 dependency warnings in 20.67s.
- Focused lifecycle/delivery/races: 8 passed, 0 failed, 1 dependency warning in 1.94s.
- Redis outage: durable FAILED record, publisher retries 1; recovery published 1; flush rebuilt 12 revocations.
- Required Redis unavailable: exit 1, `required_novaid_redis_unavailable`.
- Optional Redis unavailable: exit 0, PostgreSQL pool active and Redis client absent.
- Python 3.11.8; PostgreSQL 14.20; Redis 8.4.0; psycopg 3.3.4.
