# AfriTech Blockchain Architecture Map

Status: CANONICAL BLOCKCHAIN ANCHOR MAP

Purpose: describe how AfriTech integrates architecture anchoring into the API,
event indexing surface, dashboard, and chain verification flow.

## Operating Boundary

- Blockchain anchors prove publication only.
- They do not define truth, replay, proof authority, or settlement authority.
- Auto-anchor is an operational convenience, not a truth source.

## End-to-End Flow

```text
AfriTech API
    ↓
Architecture proof generation
    ↓
Auto-anchor hook (optional)
    ↓
ArchitectureAnchor smart contract
    ↓
Ethereum Sepolia / Base Sepolia L2 / Mainnet
    ↓
Event subscription + anchor index
    ↓
Etherscan verification packet
    ↓
Anchor dashboard
```

## API Surfaces

- `POST /v1/architecture/anchor/blockchain`
  - publishes an architecture proof to the chain
  - records a canonical anchor index entry
  - returns a verification packet for the contract surface

- `GET /public/architecture/proof`
  - can attach a live chain receipt when
    `AFRITECH_CHAIN_AUTO_PUBLISH_ON_PROOF=true`

- `GET /public/architecture/anchors`
  - read-only anchor index snapshot

- `GET /public/architecture/anchors/{anchor_id}`
  - read-only anchor detail

- `GET /public/architecture/anchors/dashboard`
  - operator-facing dashboard for anchor publication state

- `GET /public/architecture/anchors/status`
  - auto-anchor state, index snapshot, and verification readiness

- `GET /public/architecture/anchors/stream/status`
  - event subscription health and indexed event snapshot

- `GET /public/architecture/anchors/stream/replay`
  - read-only replay of recent websocket events after a stream sequence cursor

- `POST /public/architecture/anchors/stream/poll`
  - operator-triggered event backfill / poll

- `GET /public/architecture/anchors/reconciliation`
  - cross-network grouping by proof hash with observed, missing, partial, and
    divergent network state

- `GET /public/architecture/anchors/reconciliation/resolution`
  - conflict resolution semantics for each reconciled evidence set

- `GET /public/architecture/anchors/mainnet-promotion-gate`
  - mainnet promotion approval or blocking findings based on reconciliation

- `GET /public/architecture/evidence/policy`
  - formal reconciliation invariants, stream policy, and promotion rules

- `GET /public/architecture/evidence/semantics`
  - governed evidence lifecycle, transition guards, terminal states, and
    authority model with a stable semantics hash

- `GET /public/architecture/evidence/protocol`
  - combined platform, protocol, governance, validator, and public surface
    contract with a stable protocol hash

- `GET /public/architecture/anchors/explorer`
  - public handoff shell for the external React/Vite anchor explorer

- `GET /public/architecture/anchors/verification`
  - Etherscan contract verification packet

- `GET /public/architecture/anchors/verification/abi`
  - public contract ABI surface

- `GET /public/architecture/anchors/verification/source`
  - public contract source surface

- `GET /public/architecture/blockchain/map`
  - canonical machine-readable map of the blockchain subsystem

- `GET /public/architecture/adr/{adr_id}/hash`
  - governed ADR content hash packet

- `GET /public/architecture/adr/{adr_id}/contract-link`
  - ADR hash to `ArchitectureAnchor.anchorProof(string,bytes32)` link packet

## Components

### 1. AfriTech API

Publishes architecture proofs and exposes read-only anchor views.

### 2. Auto-anchor system

The proof generator can attach a live receipt without granting chain
authority to the proof surface.

### 3. Anchor indexer

Indexes publication records for dashboard and API read-back. The default
backend is in-memory, but production deployments can select file, Redis, or
Postgres persistence.

The index preserves cross-network observations for the same `anchor_id` by
using `anchor_id`, `network`, and transaction/publication identity as the
storage key. This prevents Sepolia, Base Sepolia, and Mainnet observations from
overwriting one another.

Reconciliation invariants require proof-hash grouping, anchor identity
consistency, contract consistency, required network coverage, and read-only
evidence semantics.

### 4. ArchitectureAnchor smart contract

Stores anchor hash records on-chain through `anchorProof(...)`.

### 5. Ethereum network

Current rollout path:

- Sepolia for pilot and first public verification
- Base Sepolia L2 for event-stream and scale validation
- Mainnet for promoted immutable publication

### 6. Etherscan verification packet

Packages the contract address, ABI fingerprint, source path, and explorer
links needed for external verification.

### 7. Anchor dashboard

Read-only operational dashboard for:

- latest publication
- contract verification readiness
- indexed publications
- chain health

### 8. External anchor explorer

The `anchor_explorer/` app provides a public inspection client for:

- websocket stream state and replay
- anchor detail lookup
- reconciliation status
- ADR hash and contract-link packets
- contract verification metadata
- evidence consistency policy and mainnet gate status

### 9. Mainnet promotion gate

Mainnet promotion is blocked unless reconciliation has no divergent evidence,
required pre-mainnet networks are observed, and WebSocket-first observation is
the active streaming policy. Polling remains available as operator backfill,
but it is not the primary production observation path.

## Canonical Configuration

```env
AFRITECH_CHAIN_MODE=sepolia
AFRITECH_CHAIN_PROFILE=sepolia
AFRITECH_CHAIN_ENABLE_PUBLISH=true
AFRITECH_CHAIN_AUTO_PUBLISH_ON_PROOF=true
AFRITECH_CHAIN_RPC_URL_SEPOLIA=<sepolia rpc url>
AFRITECH_CHAIN_RPC_URL_MAINNET=<mainnet rpc url>
AFRITECH_CHAIN_RPC_URL_BASE_SEPOLIA=<base sepolia rpc url>
AFRITECH_CHAIN_CONTRACT_ADDRESS=<deployed ArchitectureAnchor contract>
AFRITECH_CHAIN_ADDRESS_CHECKSUM=<publisher wallet address>
AFRITECH_CHAIN_PRIVATE_KEY_PATH=/run/secrets/eth_private_key
AFRITECH_CHAIN_INDEX_BACKEND=file|redis|postgres
AFRITECH_CHAIN_INDEX_FILE=/var/lib/afritech/anchor-index.json
AFRITECH_CHAIN_INDEX_REDIS_URL=redis://redis:6379/0
AFRITECH_CHAIN_INDEX_DATABASE_URL=postgresql://...
AFRITECH_CHAIN_EVENT_SUBSCRIBER_ENABLED=true
AFRITECH_CHAIN_EVENT_SUBSCRIBER_TRANSPORT=websocket
AFRITECH_CHAIN_EVENT_SUBSCRIBER_INTERVAL_SECONDS=30
AFRITECH_CHAIN_CONTRACT_DEPLOYMENT_BLOCK=11064832
AFRITECH_MAINNET_PROMOTION_REQUIRED_NETWORKS=sepolia,base-sepolia
```

## Authority Model

```text
Constitution
    ↓
Deterministic Truth
    ↓
Replay
    ↓
Proof
```

Blockchain anchors sit outside the authority chain. They provide immutable
publication evidence, not truth authority.

## Promotion Path

1. Deploy `ArchitectureAnchor.sol` to Sepolia.
2. Publish a live architecture anchor through the API.
3. Inspect `/public/architecture/anchors/dashboard`.
4. Verify the contract packet through `/public/architecture/anchors/verification`.
5. Enable event subscription and confirm `/public/architecture/anchors/stream/status`.
6. Confirm `/public/architecture/anchors/reconciliation` has no divergent evidence.
7. Confirm `/public/architecture/evidence/semantics` matches the governed evidence lifecycle.
8. Confirm `/public/architecture/evidence/protocol` is `READY`.
9. Confirm `/public/architecture/anchors/mainnet-promotion-gate` is approved.
10. Promote only after Sepolia and Base Sepolia evidence are reconciled.
11. Repeat on Mainnet with separate operational approval.
