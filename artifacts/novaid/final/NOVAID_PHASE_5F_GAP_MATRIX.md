# NovaID Phase 5F gap matrix

| Area | Result | Gap |
|---|---|---|
| Host publisher/consumer lifecycle | PASS focused | Long soak absent |
| Redis outage/restart/flush | PASS focused | Timeout/partial-write not reproduced |
| Metrics/trace local export | PASS | No external backend ingestion |
| Two-process revocation | PASS locally | Full positive/negative sequences incomplete |
| PostgreSQL races | PARTIAL | 2 of required matrix certified |
| Repository refactor | PARTIAL | Transitional SQL facade remains |
| Audit | PARTIAL | Full catalogue/authorization absent |
