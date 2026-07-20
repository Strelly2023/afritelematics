# NOVARIDE traceability

Release candidate: NOVARIDE-RC-001
Commit: a1b818d5513d50d9a62a1f47d14367d36aef681f
Scope: INITIAL-GA-AU-VIC-001

| Requirement | Status | Evidence | Blockers |
| --- | --- | --- | --- |
| NR-RIDER-001 Rider registration and booking | BLOCKED | artifacts/novaride/ga-readiness/TEST_RESULTS.json | live deployment approval not present |
| NR-DRIVER-002 Driver registration and acceptance | BLOCKED | artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json | physical-device certification remains external |
| NR-SAFETY-003 Safety event reporting and support workflow | BLOCKED | artifacts/novaride/operations-browser-certification/RELEASE_DECISION.md | external pilot and live deployment evidence absent |
| NR-PAY-004 Controlled cash or approved NovaPay payment handling | BLOCKED | artifacts/novaride/ga-readiness/RELEASE_GATE_RESULTS.json | approved NovaPay payment activation not yet certified |
| NR-RUNTIME-005 Operational runtime, readiness, and evidence integration | BLOCKED | artifacts/novaride/trusted-mobility-upgrade/NOVARIDE_RELEASE_CERTIFICATE.md | live PostgreSQL/Redis/Kafka proof and physical-device matrix remain external |
