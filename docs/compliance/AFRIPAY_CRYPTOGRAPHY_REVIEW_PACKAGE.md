# AFRIPAY_CRYPTOGRAPHY_REVIEW_PACKAGE

Status: external cryptography review package

## Signing scheme description
AfriPay evidence bundles are signed with RSA PKCS#1 v1.5 over SHA-256 digests of canonical JSON evidence.

## Trust assumptions
- canonical serialization is deterministic
- the public key is distributed separately from the private key
- verifiers can inspect the public key without any system access

## Threat model
- signature forgery
- evidence tampering
- replay of stale artifacts
- public key substitution

## Key lifecycle
- generation
- storage
- rotation
- revocation
- destruction

## Attack surfaces
- evidence export API
- third-party verification CLI
- public verification portal
- audit sandbox
