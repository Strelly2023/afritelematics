# Protocol Guarantees

## Security

- Ed25519 identity
- Signed proof payloads
- TLS/WSS capable transport
- Signed handshake
- Nonce replay protection
- Rate limiting

## Consensus Integrity

- Quorum required
- Malicious minority rejected
- Tampered proof rejected
- Wrong-result minority excluded

## State Integrity

- One canonical state transition per consensus result
- All validator proofs preserved in ledger block
- State reproducible from ledger history

## Operational Discipline

Pilot activation remains held until live gates pass.
