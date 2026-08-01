# NovaID signature-counter policy

A positive stored counter must strictly increase. Updates use optimistic comparison in PostgreSQL. A non-increasing positive counter or lost update marks the credential compromised and rejects authentication. Authenticators that always report zero are accepted per WebAuthn semantics without a counter guarantee.
