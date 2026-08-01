# NovaID Phase 5E test evidence

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

- Combined suite: 60 passed, 0 failed, 0 skipped, 12 warnings in 41.73s.
- Focused session/delivery/router suite: 10 passed, 0 failed, 12 warnings in 75.84s.
- PostgreSQL runtime after 0003: 3 passed, 0 failed, 1 warning in 1.65s.
- PostgreSQL races: 2 passed in 1.72s; 2 workers; 20 iterations per covered race.
- Two-process probe: exit 0; ports 58101/58102; access and refresh rejected with HTTP 401 after cross-process logout.
- Infrastructure: PostgreSQL 14.20 on 55432; Redis 8.4.0 on 56379/db 15; Python 3.11.8; psycopg 3.3.4.
