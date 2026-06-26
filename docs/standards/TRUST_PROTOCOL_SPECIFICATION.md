# NovaTech Trust Protocol Specification

A trust packet binds tenant, actor, operation, policy decision, input hash,
result hash, event identifiers, version vector, timestamp source, evidence
version, signature, and replay reference.

Trust levels are monotonic only when their required proof is present:
authenticated, policy verified, evidence produced, replay verified, federated
verified, publicly verifiable. A verifier MUST recompute canonical hashes,
verify signature lineage and key status, validate schemas, enforce tenant
binding, and reject unsupported versions.

Evidence is immutable and append-only. Revocation, correction, or supersession
creates a new signed record linked to the original. Verification is side-effect
free. Public verification bundles MUST contain enough material to verify without
private database access and MUST disclose no secret or excess personal data.
