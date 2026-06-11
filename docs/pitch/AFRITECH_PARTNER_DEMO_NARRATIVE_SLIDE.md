# AfriTech Partner Demo Narrative Slide

Status: PARTNER DEMO NARRATIVE SLIDE

Classification: PARTNER_FACING_SINGLE_SLIDE_STORY_SURFACE

Purpose: provide a one-slide narrative for partner meetings that explains what
AfriTech proves, how it proves it, and why the public proof surfaces matter.

## Slide Title

AfriTech: A system that proves its own integrity

## Slide Headline

From architecture to governance to public verification, AfriTech exposes a
cryptographically anchored proof that the system is running within its declared
boundaries.

## Slide Flow

1. Architecture is governed
   ADR -> RULE -> BIND -> GUARD -> CI
2. Runtime startup is verified
   FastAPI startup stays clean and bounded from Django authority
3. Proof artifacts are generated
   Runtime scan + architecture graph + governance chain hashes
4. Proof is anchored
   Anchor commitment + publication envelope + public chain receipt
5. Partners verify independently
   `/public/architecture/proof` -> `/public/architecture/chain/{anchor_id}` -> `/public/verify/{anchor_id}`

## Key Messages

- We do not ask partners to trust a dashboard.
- We let partners verify a bounded proof packet.
- The anchor proves publication and export integrity only.
- Replay and governed execution remain the authority.

## Speaker Notes

- Start with the problem: most platforms expose claims, not proofs.
- Show the architecture proof endpoint and the chain receipt endpoint.
- Show the same anchor id resolving in public verification.
- Close with the operator integrity dashboard to show internal and external views align.

## Bounded Claim

This narrative does not claim that public chains replace replay, that public
verification grants authority, or that the dashboard defines truth.
