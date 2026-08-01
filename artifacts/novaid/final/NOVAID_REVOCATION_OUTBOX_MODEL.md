# NovaID revocation outbox model

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Migration `0002_novaid_runtime.sql` creates `novaid_security_outbox` with PENDING, PUBLISHED, FAILED, and DEAD_LETTER states. Tests prove commit durability, failure accounting, publication state, and rejection of token/secret payload keys. A background publisher and Redis consumer remain incomplete.
