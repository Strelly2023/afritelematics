# NovaID authenticator lifecycle

Supported transitions cover active, suspended, revoked, compromised, and deleted credentials. Status history is durable and tenant scoped. Revocation propagation through Redis/outbox, administrative authorization, and governed recovery remain incomplete.
