# Interim General Availability PRR

Decision: **NO-GO**

This is an interim assessment, not a release certificate. No immutable release
candidate has been selected because the deployed EC2 checkout and images do
not match the validated recovery branch.

## Passed evidence

- `UNIT_TESTED`: mounted production route and OpenAPI uniqueness plus affected
  route contracts, 47 passed.
- `UNIT_TESTED`: focused security, NovaID, session, and AfriPay security tests,
  27 passed. This is not a complete static or dynamic security certification.
- `STAGING_TESTED`: NGINX syntax, `/healthz`, known-host redirects, and
  unknown-host rejection were observed on EC2.

## Blocking evidence

| ID | Severity | Owner | Required closure evidence |
| --- | --- | --- | --- |
| GA-DEPLOY-001 | High | Platform Operations | Clean named RC checkout; independently deployed required services; immutable image digests matching the RC. |
| GA-TLS-001 | High | Platform Operations | Trusted certificates whose SANs include every exact nested production hostname. |
| GA-SEC-001 | High | Security | Complete source, dependency, container, authenticated and unauthenticated dynamic scans with no unresolved Critical or High findings. |
| GA-MOBILE-001 | Blocked | Mobile QA | Physical Android and iOS evidence tied to signed Rider and Driver artifacts. |
| GA-PROVIDER-001 | Blocked | Integration Owners | Provider sandbox/live execution, callback verification, reconciliation and required approvals. |
| GA-PERF-001 | Blocked | Performance Engineering | Predeclared SLOs plus deployed load, peak, burst and soak results. |
| GA-RECOVERY-001 | High | SRE / Data | Executed backup restore, dependency failover, rollback, measured RPO/RTO and alert evidence. |
| GA-SIGN-001 | Blocked | Release Management | Deterministic manifest, organisational signature verification, and required approvals. |

## Additional findings

- The live EC2 checkout was `f2ff9538a`, ahead 3 and behind 11, with untracked
  artifacts. It is not an acceptable deployment source.
- The active application images are tagged `latest`; no RC digest binding was
  demonstrated.
- `api.novapay.afritechnology.com`, `api.novaride.afritechnology.com`, and
  `api.novalogistics.afritechnology.com` receive a certificate whose SAN list
  does not contain those names.
- Repository-wide `PYTHONWARNINGS=error` is blocked during application import
  by an existing Pydantic class-based configuration deprecation. Duplicate
  operation warnings are independently asserted absent by the route test.

No evidence manifest or signature is asserted for this interim assessment.
