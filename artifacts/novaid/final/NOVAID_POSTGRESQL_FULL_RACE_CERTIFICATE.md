# NovaID PostgreSQL full race certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Not a full certificate. Registration idempotency and outbox claim pass with 2 workers × 20 iterations under READ COMMITTED. Deadlocks 0; serialization failures 0; lock timeouts 0; retries 0. Remaining prescribed races were not executed.
