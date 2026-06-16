# AfriTech Feature-to-Proof Matrix

## Classification

```text
STATUS: CANONICAL FEATURE EVIDENCE MATRIX
CLASSIFICATION: GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY
GENERATION: REPLAY_DERIVED_EVIDENCE_PROJECTION
ROLE: TIE CLAIMED FEATURES TO IMPLEMENTATION, TEST, REPLAY, PROOF, AND BOUNDARY GUARD EVIDENCE
AUTHORITY: NON-RUNTIME; DOES NOT AUTHORIZE LIVE PILOT OR PRODUCTION EXECUTION
```

This matrix completes the P0 roadmap item:

```text
FEATURE -> TECHNICAL STATUS -> ACTIVATION STATUS -> ARTIFACT EVIDENCE -> JSON/PROOF VALIDATION -> BOUNDARY GUARD -> CI ENFORCEMENT -> VERSIONED CLAIM HISTORY
```

The executable source of truth is `afritech/features.py`. Candidate features do
not become exported registry features unless the evidence index proves the
required implementation, test, replay, proof, boundary guard, and dependency
chain.

| Feature | Technical status | Activation status | Boundary guard | Evidence basis |
| --- | --- | --- | --- | --- |
| Trust Kernel | IMPLEMENTED | GATED | `afritech/ci/trust_lock_validator.py` | implementation, tests, replay, proof, boundary guard |
| AfriTPPS Execution | IMPLEMENTED | GATED | `afritech/ci/afritpps_execution_validator.py` | implementation, tests, replay, proof, boundary guard |
| Cross-Domain Orchestration | IMPLEMENTED | GATED | `afritech/ci/execution_integrity_validator.py` | implementation, tests, replay, proof, boundary guard |
| Federation | IMPLEMENTED | GATED | `afritech/ci/network_determinism_validator.py` | implementation, tests, replay, proof, boundary guard |
| Resilience Hardening | IMPLEMENTED | GATED | `afritech/ci/resilience_hardening_validator.py` | implementation, tests, replay, proof, boundary guard |
| AfriPower Intelligence | IMPLEMENTED | GATED | `afritech/ci/afripower_intelligence_validator.py` | implementation, tests, replay, proof, boundary guard |
| Governance Chain | IMPLEMENTED | GATED | `afritech/ci/binding_completeness_validator.py` | implementation, tests, replay, proof, boundary guard |
| Classification CI | IMPLEMENTED | GATED | `afritech/ci/production_readiness_certificate_validator.py` | implementation, tests, replay, proof, boundary guard |
| Pilot Gates | IMPLEMENTED | CONTROLLED_PILOT_READY | `afritech/ci/afriride_pilot_execution_checklist_validator.py` | implementation, tests, replay, proof, boundary guard |
| Domain Surfaces | PARTIAL | GATED | `afritech/ci/surface_state_resolution_validator.py` | implementation, tests, replay, proof, boundary guard |
| Legal Evidence Export | IMPLEMENTED | GATED | `afritech/ci/afriride_stakeholder_evidence_report_validator.py` | implementation, tests, replay, proof, boundary guard |
| Operational Tooling | IMPLEMENTED | GATED | `afritech/ci/observability_authority_validator.py` | implementation, tests, replay, proof, boundary guard |

## API Surface

The registry is available to operator tooling at:

```text
/api/feature-registry
/v1/feature-registry
```

External partner validation is available at:

```text
/public/feature-registry
/public/feature-registry/verify
/public/feature-registry/portal
/public/trust-infrastructure
/public/trust-infrastructure/verify
/public/global-verification
/public/global-verification/verify
/public/global-verification/portal
/public/ecosystem-evolution
/public/ecosystem-evolution/verify
/public/ecosystem-evolution/standard
/public/ecosystem-evolution/portal
```

Local verifier CLI:

```bash
python3 -m afritech.cli.main verify --registry --json
python3 -m afritech.cli.main verify --global --json
python3 -m afritech.cli.main verify --ecosystem --json
```

The endpoint is read-only, role-gated, and returns:

- generation mode
- candidate feature count
- registry classification
- feature count
- completion count
- production-ready count
- activation flags
- versioned claim history path
- feature hash
- evidence hash
- registry hash
- Ed25519 integrity signature
- per-feature evidence and validation summaries

## CI Enforcement

The local and GitHub CI entrypoint is:

```bash
pytest afritech/tests/test_features.py -q
```

## Activation Boundary

The matrix does not change the system status:

```text
live_pilot_authorized = false
production_proven = false
economic_activation_allowed = false
```

Feature completeness means the repository has a stable, test-backed, boundary
guarded claim map. It does not mean every planned product surface is implemented
or authorized for live users.

## Level 12 Rule

```text
Feature candidates may be declared for review.
Only evidence-derived candidates can exist in the exported registry.
External exports are signed and verifier-checkable.
Federated trust certificates require partner/government-capable quorum verification.
```

## Level 14 Trust Infrastructure

```text
Signed registry
-> governed signer trust registry
-> revocation check
-> federated trust witnesses
-> partner/government public verification portal
```

## Level 15 Global Public Verification

```text
Signed registry
-> federated trust certificate
-> cross-network anchor receipts
-> optional on-chain anchoring support
-> globally portable verification bundle
```

Level 15 means exported truth can be checked without trusting the system that
generated it. The global bundle binds the registry hash to federated witnesses
and independent network receipts while preserving the existing activation
boundary.

## Level 16 Ecosystem Trust Infrastructure

```text
Global verification bundle
-> multi-organization adoption certificate
-> cross-government adoption profiles
-> live public-ledger publication path
-> interoperable verification standard export
```

Level 16 is ecosystem evolution, not runtime authorization. It proves that the
verification layer can be adopted by multiple organizations, reviewed by
government observers, anchored to public ledgers through a live publication path,
and implemented by external parties using a stable verification standard.

Final guarantees:

- no fake feature can exist
- no incomplete feature can appear
- no unverifiable claim can be exported
- no production state can be falsely implied
- no untrusted party can sign truth
- no revoked authority can persist
- federated quorum is required for trust-infrastructure verification
- cross-network interoperability is required for global verification
- optional on-chain anchoring is supported but not required for CI or local verification
- truth can exist independently of the system that generated it
- multi-organization trust networks are certificate-bound
- cross-government adoption is represented as observer/reviewer profiles
- live public-ledger anchoring is supported through an explicit protected publication path
- interoperable verification standards are exported for external implementers
