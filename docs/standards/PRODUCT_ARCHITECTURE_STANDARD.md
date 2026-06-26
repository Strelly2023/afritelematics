# NovaTech Product Architecture Standard

Products are Layer 7 domain surfaces. They MAY own domain entities, workflows,
rules, projections, and user experience. They MUST consume NovaID, NovaPower,
governed execution, NovaTrust, NovaReplay, NovaFederation, shared payment rails,
and platform observability through versioned contracts.

Products MUST NOT create independent identity, signing, evidence, replay,
payment-settlement, federation, or policy engines. A product manifest declares
owner, lifecycle, capabilities consumed, data classes, tenant model, APIs,
events, SLOs, threat model, and retirement plan.

Promotion gates:

- Prototype: owner, threat sketch, schemas, isolated environment.
- Pilot: policy, evidence, replay, telemetry, operator runbook.
- Production: security review, SLO/error budget, RTO/RPO, rollback, on-call.
- Certified: independent control and evidence review.
- Federated: peer policy, trust roots, protocol compatibility, isolation tests.
- Retired: migration complete, access removed, evidence retained by policy.
