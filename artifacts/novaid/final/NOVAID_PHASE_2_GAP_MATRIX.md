# NovaID Phase 2 gap matrix

| Gate | Result | Evidence / gap |
|---|---|---|
| G1 Domain | PASS | lifecycle and policy tests |
| G2 Persistence | PARTIAL | normalized local adapter and PostgreSQL DDL; PostgreSQL not executed |
| G3 Tenant isolation | PARTIAL | tenant-bound identity repository negative test; remaining repositories not integrated |
| G4 Credential security | PARTIAL | Phase 1 hasher; durable lifecycle service incomplete |
| G5 Session security | PARTIAL | normalized schema and Phase 1 local revocation; service integration incomplete |
| G6 Replay protection | PARTIAL | Phase 1 local atomic tests; durable rotation integration incomplete |
| G7 Authentication policy | PASS | deterministic fail-closed tests |
| G8 Audit evidence | PASS | transactional rollback and secret rejection tests |
| G9 Migration verification | PARTIAL | local empty-schema validation only |
| G10 PostgreSQL | NOT_EXECUTED | no configured test instance |
| G11 Distributed revocation | BLOCKED | shared backend not configured |
| G12–G20 | BLOCKED | ceremonies/providers/infrastructure/devices/resilience/accessibility/E2E/assessment unavailable |
