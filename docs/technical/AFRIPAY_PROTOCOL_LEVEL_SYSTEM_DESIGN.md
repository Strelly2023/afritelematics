# AfriPay Protocol-Level System Design

## 1. Public Protocol

AfriPay is modeled as a public financial protocol with four verifiable commitments:

1. Transaction commitment
   - every payment produces a transaction-level reconciliation report
   - every report is bound to a Merkle inclusion proof
   - every inclusion proof is bound to a ZK-style attestation

2. Global commitment
   - all transaction proofs are aggregated into a global proof
   - the global proof is deterministic and replay-safe
   - the global proof can be anchored externally or on-chain

3. BFT consensus commitment
   - node votes are collected in PBFT / Tendermint-style phases
   - finality requires pre-prepare, prepare, and commit thresholds
   - consensus certificates are hash-addressed and replay-verifiable

4. Chain commitment
   - the anchored proof hash is verified through the smart-contract surface
   - the chain receipt is treated as evidence, not as system truth

## 2. Protocol Flow

Payment -> reconciliation -> Merkle inclusion proof -> recursive global proof -> consensus certificate -> anchor -> on-chain verification

The protocol is intentionally layered:

- ledger state is the source of financial truth
- proof layers attest to that truth
- consensus layers confirm distributed agreement
- chain layers preserve external evidence

## 3. Product Launch Architecture

### Client surfaces

- mobile wallet
- merchant dashboard
- admin and audit console
- partner API

### Service surfaces

- payments
- treasury
- reconciliation
- consensus
- proof export
- chain anchoring
- observability

### Launch posture

- private pilot
- controlled partner rollout
- regulator-facing sandbox
- audit export readiness

## 4. Investor and Regulatory Dossier

### Investor questions answered

- What is the moat?
  - verifiable financial infrastructure with proof-carrying execution

- Why is it defensible?
  - distributed reconciliation, protocol-level proofs, and deterministic anchoring

- Why does it scale?
  - BFT finality, recursive proof aggregation, and low-cost verification

### Regulatory questions answered

- Can transactions be audited?
  - yes, through deterministic reconciliation and proof export

- Can failures be reconstructed?
  - yes, through append-only event chains and replay-safe proofs

- Can anchors be verified externally?
  - yes, through chain receipts and smart-contract verification calls

## 5. Current Boundary

AfriPay is protocol-ready inside the repository.
Live network settlement, chain anchoring, and production provider proofs remain environment-gated and fail-closed.
