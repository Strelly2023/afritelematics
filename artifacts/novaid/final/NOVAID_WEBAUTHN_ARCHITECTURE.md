# NovaID WebAuthn architecture

The authoritative API delegates to `WebAuthnService`. Challenges are random, stored only as SHA-256 hashes, tenant/user/purpose/RP/origin bound, single-use, and expiring. The `webauthn` library validates client data, authenticator data, origin, RP ID, user verification, COSE key, and signatures. PostgreSQL stores credentials, authenticators, bindings, attestation records, and status history.
