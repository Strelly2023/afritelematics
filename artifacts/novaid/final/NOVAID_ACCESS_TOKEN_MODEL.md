# Access-token model

Tokens carry issuer, audience, subject, JTI, IAT, NBF, expiry, tenant, session, membership, authentication strength, security version, and token version. HS256 is server-selected; signatures use a minimum 32-byte configured key. Validation checks durable identity, membership, session and security version plus revocation. Tokens are never persisted.
