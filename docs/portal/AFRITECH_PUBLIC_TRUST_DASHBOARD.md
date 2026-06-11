# AfriTech Public Trust Dashboard

Status: PUBLIC TRUST DASHBOARD

Classification: EXTERNAL_READ_ONLY_TRUST_SURFACE

Purpose: define the public dashboard surface that lets partners, auditors, and
observers inspect architecture proof, chain publication, and public
verification without receiving any execution authority.

## Endpoint

- `GET /public/trust/dashboard`

## Dashboard Sections

1. integrity headline
   runtime boundary status, proof id, anchor id, publication id
2. chain publication
   deterministic receipt, Sepolia publication, and Mainnet promotion posture
3. public verification
   public verify path, public registry path, system integrity demo path, and chain networks path
4. verifier distribution
   `afritech-verify` and `afritech-verify-session`
4. bounded claim
   replay and governed execution remain the authority

## Required Surfaces

- `/public/architecture/proof`
- `/public/architecture/chain/{anchor_id}`
- `/public/architecture/chain/networks`
- `/public/verify/{anchor_id}`
- `/public/demo/system-integrity`

## Deployment Notes

- the UI can be hosted as a static React surface
- it must consume only public endpoints
- it must not request operator credentials
- Sepolia is the default first live publication surface before Mainnet promotion

## Bounded Claim

The public trust dashboard is a read-only trust surface.

It does not:

- mutate runtime
- replace replay
- grant governance authority
- elevate public chain publication into truth authority
