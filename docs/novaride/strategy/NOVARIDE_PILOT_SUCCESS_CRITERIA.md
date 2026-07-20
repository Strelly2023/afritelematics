# NovaRide pilot success criteria

| Measure | Initial target | Evidence source |
|---|---:|---|
| Rider registration completion | >= 95% | Identity funnel telemetry |
| Approved-driver onboarding completion | >= 90% | Onboarding workflow telemetry |
| Ride-request success | >= 95% | Booking events |
| Driver-assignment success during operating hours | >= 90% | Dispatch events |
| Median assignment time | < 30 seconds | Dispatch latency metric |
| Completed trips among started trips | >= 95% | Trip state audit |
| Payment recording success | >= 99% | Payment/reconciliation ledger |
| Crash-free sessions | >= 99% | Mobile crash telemetry |
| Critical safety workflow success | 100% in controlled tests | Safety drill evidence |
| Duplicate payment or trip creation | 0 | Idempotency/audit checks |
| Cross-user data exposure | 0 | Access-control/security evidence |
| Unresolved critical defects | 0 | Release defect register |

These are pilot hypotheses, not fabricated outcomes. Baselines require a defined population, operating window and region. Every metric must identify numerator, denominator, exclusions, owner, alert threshold and evidence retention. No promotion decision may substitute test fixtures for field performance.
