# Card Provider Outage Runbook

Detection: provider health degraded, fallback spike, payment failures.
Impact: card authorization may fail; rides continue through wallet, mobile money, or cash fallback where approved.
Immediate actions: probe provider, open circuit if failure persists, drain provider, route to fallback.
Approval: required for payment-provider switch in production.
Commands: `POST /v1/novaride/operations/providers/{id}/drain`, `POST /v1/novaride/operations/circuits/{circuit}/open`.
Verification: provider route evidence, no duplicate payment intents, outbox published.
Rollback: restore provider and close circuit after successful half-open probes.
Escalation: Payment Operations then SRE.
Evidence: route decision hash, circuit receipt, incident timeline.
Closure: primary or approved fallback stable for 30 minutes.
