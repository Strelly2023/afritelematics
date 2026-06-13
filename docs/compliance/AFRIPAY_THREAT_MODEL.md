# AFRIPAY_THREAT_MODEL

Threat model for AfriPay evidence and verification surfaces.

## Insider threats
- privileged operator misuse
- evidence mutation before export
- credential misuse

## Key compromise
- private key theft
- public key substitution
- revocation bypass

## Provider compromise
- callback spoofing
- duplicate delivery storms
- silent provider failure

## Replay attacks
- stale evidence re-submission
- repeated webhook replay
- repeated anchor submission

## Evidence forgery
- forged signature
- modified artifact contents
- partial bundle truncation

## Anchor corruption
- incorrect chain receipt
- mismatched anchor hash
- falsified on-chain verification
