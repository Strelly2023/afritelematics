# AfriRide Multi-Organization Trust Network Activation

Status: MULTI-ORG TRUST NETWORK ACTIVATION PLAN
Classification: GOVERNED FEDERATION ACTIVATION SURFACE

Purpose: define how AfriRide moves from single-operator proof surfaces to a
multi-organization trust network for partners, auditors, fleets, and public
verification observers.

This plan does not make the trust network truth authority. Replay, receipts,
evidence bundles, and signed verification artifacts remain the authority chain.

## Network Thesis

AfriRide trust becomes stronger when independent organizations can verify the
same ride, receipt, replay, and evidence surfaces without controlling the
originating runtime.

```text
operator -> receipt -> registry -> verifier -> partner/auditor observer
```

## Participant Classes

- Operator organization: runs rider and driver operations.
- Fleet partner: supplies drivers, vehicles, or local dispatch capacity.
- Verifier organization: validates receipts, replay hashes, and evidence bundles.
- Auditor organization: packages verification results for diligence or compliance.
- Public observer: reads public trust artifacts without mutation rights.

## Trust Network Responsibilities

- onboard organizations with bounded trust-domain metadata
- publish trust registry entries
- exchange signed receipt and certificate references
- expose verification APIs and SDK flows
- preserve organization-level trust score history
- support external audit package export

## Non-Responsibilities

- the trust network does not mutate rides
- the trust network does not approve trips
- the trust network does not execute settlement
- the trust network does not override replay authority
- the trust network does not create production claims without field evidence

## Activation Phases

### Phase 1: Single Operator Verification

```text
AfriRide operator -> public receipt verification
```

Exit criteria:

- receipts are emitted for demo rides
- replay hashes verify
- evidence viewer is accessible
- public verification endpoint returns a bounded result

### Phase 2: Partner Verifier Onboarding

```text
AfriRide operator -> partner verifier -> verification result
```

Exit criteria:

- partner organization profile exists
- verifier API key or signed verifier identity exists
- partner can verify receipt and replay hash
- failed verification produces a fail-closed result

### Phase 3: Multi-Org Trust Exchange

```text
operator -> fleet partner -> auditor -> public observer
```

Exit criteria:

- trust exchange records include issuer organization, subject organization, receipt hash, and trust score
- registry entries can be independently read
- audit package can be exported without runtime mutation
- organization trust dashboard distinguishes operator, verifier, auditor, and observer roles

### Phase 4: Enterprise Network Mode

```text
fleet trust -> risk trends -> compliance reports -> partner dashboard
```

Exit criteria:

- fleet-level trust summaries exist
- driver trust scores are evidence-derived
- risk trends are separated from proof authority
- compliance report export is available for enterprise review

## Required API Surfaces

- `GET /public/trust/{receipt_id}`
- `POST /v1/trust/network/verify`
- `POST /v1/partner/verify`
- `GET /v1/novascript/trust/graph`
- `POST /v1/novascript/federation/trust-exchange`

## Required UI Surfaces

- `Verified Ride (Trust Score: 92)`
- `Verify this ride`
- `Driver Trust Score`
- `Download Verification Package`
- `Trust Network`
- `Fleet Trust`
- `Risk Trends`
- `Compliance Reports`

## Launch Guardrails

- No organization may claim replay authority.
- No partner may mutate ride state through verification APIs.
- No trust score may be displayed without a linked receipt or evidence source.
- No public portal may expose secrets, tokens, private rider data, or driver private data.
- No multi-org claim may be used in sales material until at least one partner verifier has completed a bounded verification flow.
