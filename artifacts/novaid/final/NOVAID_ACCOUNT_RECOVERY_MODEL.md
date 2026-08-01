# NovaID account recovery model

Recovery requests are tenant bound and externally generic. A one-time recovery code produces evidence, a different active tenant security administrator approves, and completion increments security version, revokes sessions/refresh families/codes, suspends active WebAuthn credentials, and writes an outbox event. Rate limiting, multiple approvals, cancellation/expiry workers, and alternate evidence remain incomplete.
