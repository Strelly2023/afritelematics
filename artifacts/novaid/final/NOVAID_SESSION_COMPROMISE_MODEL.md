# Session compromise model

Containment marks the tenant-bound session COMPROMISED, revokes its active refresh families, increments identity security version, commits durable state, then publishes shared session revocation. Compromised sessions cannot validate or refresh.
