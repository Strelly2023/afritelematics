# NovaScript Governance Handbook

This handbook is the operational reference for NovaScript governance.

For the full administrator and staff operating reference, see
`docs/governance/NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md`.

## Policy Registry

The policy registry stores policies as versioned governance code. Each policy has:

```text
policy_id
name
version
policy_hash
status
```

## Policy Versions

Every decision links to the policy version and hash used during evaluation. This preserves policy provenance when policies evolve.

## Decision Evaluation

Evaluation inputs include:

```text
trust_score
risk_score
federation_verified
receipt_verified
```

Output:

```text
allowed
decision_id
policy_id
policy_version
policy_hash
```

## Approval Flow

```text
request
-> policy evaluation
-> trust review
-> receipt issue
-> certificate chain
-> assurance
-> audit or public verification
```

## Governance Receipts

Receipts prove that a governed decision occurred. They include prompt/output hashes, trust score, status, sequence, and deterministic signature.

## Audit Chain

The audit chain is:

```text
policy decision
-> governance receipt
-> certificate chain
-> assurance report
-> portable verification package
-> public verification
```

## Boundary

Governance defines whether an artifact satisfies NovaScript trust controls. It does not replace legal review, government approval, or production incident authority.
