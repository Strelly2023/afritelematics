# NovaID core authentication local certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

This is a **local integration certificate**, not production certification and not GA certification.

The 60-test local suite passed against isolated PostgreSQL 14.20 and Redis 8.4.0. Two real Uvicorn processes on ports 58101 and 58102 verified cross-process validation, refresh, logout, and stale access/refresh rejection. This remains a partial local certificate because the complete race/outage matrices, audit catalogue, repository refactor, and production telemetry export are absent.
