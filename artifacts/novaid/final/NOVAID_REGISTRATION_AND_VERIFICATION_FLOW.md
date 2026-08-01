# Registration and verification

Registration atomically writes pending identity, membership, scrypt credential, hashed email-verification challenge, tenant-bound idempotency record, and events. Verification atomically consumes the challenge and activates the identity. The verification code is returned only by the deterministic test-facing service; production delivery integration remains required.
