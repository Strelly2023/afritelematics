# NovaID resource lifecycle certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

FastAPI lifespan starts/stops publisher and consumer, closes Redis and PostgreSQL resources, and exposes liveness/readiness. Focused tests detect no newly leaked named background thread. Long soak and repeated production-process cycles remain incomplete.
