# Ecosystem Graduation Roadmap

STATUS: FUTURE GOVERNANCE

AfriTech scales by graduating one bounded domain at a time into the proof system.

## Status Classification

| Ecosystem | Status |
| --- | --- |
| AfriRide | ACTIVE |
| AfriHealth | FUTURE |
| AfriAgro | FUTURE |
| AfriHome | FUTURE |
| AfriLife | FUTURE |
| AfriEats | FUTURE |
| AfriPay | FUTURE |
| AfriWork | FUTURE |

Only AfriRide is currently proof-active.

## Graduation Rule

A future ecosystem must not appear in proof claims until it has executable evidence.

Passenger and driver applications for AfriRide are future implementation surfaces. They may describe interaction flows or API contracts, but they must not expand the proof claim or redefine system correctness.

The Phase 1 mobile-ready MVP plan is documented as a future implementation surface in [AfriRide GA Elite MVP](../vision/AfriRide_GA_Elite_MVP.md).

Minimum graduation requirements:

- domain-specific continuity scenario
- deterministic executor integration
- replay trace and replay verification
- identity continuity checks
- validator entry or validator group coverage
- tests in the relevant ecosystem test surface
- claim discipline policy entry with scope, evidence, validator, and counter-test

## Growth Sequence

The intended scaling path is:

```text
AfriRide proof domain
-> additional bounded domain
-> reused execution and replay guarantees
-> domain-specific continuity validators
-> multi-domain continuity runtime
```

## Operating Rule

Vision lives in docs.

Proof lives in the system.

They must remain separate until executable validation closes the gap.
