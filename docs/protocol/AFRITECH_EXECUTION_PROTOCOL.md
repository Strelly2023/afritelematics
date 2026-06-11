# AfriTech Execution Protocol

Status: EXECUTION PROTOCOL SPECIFICATION
Classification: EXTERNAL_VERIFICATION_PROTOCOL_SURFACE

Purpose: define the canonical rules for authority-bound trace hashing, replay,
receipt construction, authority sealing, and independent proof verification.

This protocol describes verification behavior.
It does not redefine constitutional or replay authority.

## Hash Rules

- Hash algorithm: `SHA-256`
- Canonical encoding: JSON with sorted keys and compact separators `(",", ":")`
- `authority_hash = H(doc_id + doc_version + governed_invariants)` through the
  canonical authority payload.
- `event_hash = H(event fields + previous_hash + authority_hash)`
- `replay_hash = H(reconstructed replay payload + authority_hash)`
- `receipt_hash = H(receipt payload + authority_hash)`
- `execution_fingerprint = H(replay_hash + receipt_hash + authority_hash)`

## Authority Model

- `doc_id` identifies the governing registered documentation surface.
- `doc_version` identifies the active doctrine version.
- `governed_invariants` identifies the invariant set bound to the execution surface.
- Every emitted `authority_hash` must resolve to
  `afritech/governance/authority_snapshots/{authority_hash}.json`.

## Trace Rules

- Every trace event must be hashed with the same `authority_hash`.
- Mixed-authority traces are invalid.
- Recomputed event hashes must match stored hashes.

## Replay Rules

- Replay reconstructs state only from persisted trace events.
- Replay authority is declared, versioned, and sealed.
- Identical trace plus identical doctrine must yield identical `replay_hash`.

## Receipt Rules

- Receipts are derived from verified evidence and replay outputs.
- `receipt_hash` must commit to `authority_hash`.
- `execution_fingerprint` binds replay, receipt, and doctrine into one stable
  proof identity.

## Cross-Artifact Consistency

The verifier must enforce:

- `trace.authority_hash == replay.authority_hash`
- `replay.authority_hash == evidence.authority_hash`
- `evidence.authority_hash == receipt.authority_hash`

Any mismatch is a verification failure.

## Version Compatibility

- Protocol version compatibility is declared in
  `afritech/governance/document_registry.yaml` under `protocol_compatibility`.
- The current protocol version is `1.0.0`.
- `1.0.0` verifiers may verify `1.0.0` and `1.0.x` proof bundles only when the
  compatibility matrix declares them compatible.
- `2.0.0` is a breaking boundary and must be rejected by `1.x` verifiers.

## Ecosystem Integration Roles

External systems may integrate with the protocol only through declared roles.

Declared roles include:

- publisher
- verifier
- auditor
- observer
- settlement adapter
- registry mirror

Each integration must declare:

- organization or system identifier
- supported protocol version
- packets published or consumed
- failure handling for mismatch or rejection

Undeclared role expansion is invalid.

## Smart Contract Boundary

Smart contracts are optional downstream protocol consumers.

Permitted contract uses:

- anchoring verified packet hashes
- storing registry checkpoint commitments
- releasing escrow after successful verification
- storing quorum attestation references

Forbidden contract uses:

- reconstructing replay state
- asserting authority outside governed doctrine
- accepting unverifiable packets as valid

Contracts may depend on protocol verdicts.
Protocol validity may not depend on contract execution.

## Public Verifier Tooling

- Public verifier entrypoint: `python -m afritech.verify`
- Direct module entrypoint: `python -m afritech.verify.verify_proof`
- Shell wrapper: `./scripts/run_public_verifier.sh <packet.json>`
- Public bundle schema:
  `afritech/verify/public_verifier_bundle.schema.json`

## Independent Verification Procedure

1. Load the proof packet.
2. Recompute `authority_hash`.
3. Load the matching authority snapshot.
4. Check protocol version compatibility.
5. Recompute event hashes and trace chain.
6. Recompute replay.
7. Recompute evidence.
8. Recompute receipt.
9. Recompute `execution_fingerprint`.
10. Emit a binary verdict: `valid` or `invalid`.
