# AfriTech Feature Claim History

## v1 - 2026-06-16

Classification:

```text
CONTROLLED_PILOT_READY_SYSTEM
GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY
REPLAY_DERIVED_EVIDENCE_PROJECTION
FEATURE_REGISTRY_LEVEL_12
LEVEL_14_FEDERATED_TRUST_NETWORK
LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER
LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE
```

Changes:

- Feature evidence registry introduced
- Feature claims bound to implementation, tests, replay, proof, and boundary evidence
- Dual status model introduced: technical status and activation status
- Required evidence validation added for path existence, non-empty files, JSON validity, proof payload shape, and boundary guards
- Evidence index auto-scanner introduced
- Feature candidates now become exported features only after evidence projection succeeds
- Registry hash, feature hash, and evidence hash introduced
- Ed25519 registry signature introduced
- Public feature registry trust portal introduced
- `afritech verify --registry` introduced for external verifier workflows
- Trust-root signing provider abstraction introduced
- Governed signer registry with revocation checks introduced
- Multi-node federated trust certificate introduced for partner and government validation
- Public trust infrastructure portal introduced
- Cross-network interoperability layer introduced
- Optional on-chain anchor receipts introduced as public verification artifacts
- Global public verification bundle introduced so registry truth can be exported and verified independently of the originating system
- Multi-organization ecosystem trust certificate introduced
- Cross-government adoption profiles introduced
- Live public-ledger anchoring path introduced for authorized publication
- Interoperable verification standard export introduced
- Machine-readable claim snapshot introduced at `reports/feature_registry_history/v1.json`
- `/api/feature-registry` exposed for AfriRide operator tooling
- Feature Registry Dashboard UI added to the operator dashboard
- Production activation remains gated

Authorization:

```text
live_pilot_authorized: false
production_ready: false
economic_activation_allowed: false
```

Snapshot:

```text
reports/feature_registry_history/v1.json
reports/registry_snapshots/v1.json
```

Public trust infrastructure:

```text
/public/trust-infrastructure
/public/trust-infrastructure/verify
/public/feature-registry/portal
/public/global-verification
/public/global-verification/verify
/public/global-verification/portal
/public/ecosystem-evolution
/public/ecosystem-evolution/verify
/public/ecosystem-evolution/standard
/public/ecosystem-evolution/portal
```

Level 15 verification:

```text
afritech verify --global --json
truth_independent_of_origin_system: true
cross_network_interoperable: true
optional_onchain_anchoring_supported: true
```

Level 16 verification:

```text
afritech verify --ecosystem --json
multi_organization_trust_networks: true
cross_government_adoption_ready: true
live_public_ledger_anchoring_supported: true
interoperable_verification_standard_exported: true
```
