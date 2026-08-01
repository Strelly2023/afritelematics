# NovaID Redis failure recovery certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Verified: required-mode startup failure, optional fallback, publication failure after database commit, retained outbox, one retry, Redis restart, successful republish, database flush, and reconstruction of 12 revocations. Timeout, partial write, and extended reconnect-loop cases remain incomplete.
