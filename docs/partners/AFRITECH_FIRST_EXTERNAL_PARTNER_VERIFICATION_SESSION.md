# AfriTech First External Partner Verification Session

Status: PARTNER SESSION RUNBOOK

Purpose: define the first external verification walkthrough as a repeatable,
evidence-producing session.

## Session Goal

Allow a partner to independently verify:

- the architecture proof packet
- the public chain receipt
- the public trust dashboard
- the bounded claim that public publication is not runtime truth

## Session Flow

1. open `/public/architecture/proof`
2. resolve `/public/architecture/chain/{anchor_id}`
3. inspect `/public/trust/dashboard`
4. open `/public/demo/system-integrity`
5. run `afritech-verify`
6. run `afritech-verify-session`
7. archive the JSON report

## Expected Outcome

- proof verification status: `VERIFIED`
- chain receipt status: `READY`
- dashboard status: `READY`
- demo readiness: `PARTNER_READY`
- partner session outcome: `PASSED`

## Promotion Rule

If the first external partner verification session passes on Sepolia, the next
governed action is `promote_to_mainnet` readiness review.
