# AfriRide Risk Control Register

Status: ACTIVE PILOT CONTROL DOCUMENT

| Risk | Control | Stop Condition |
| --- | --- | --- |
| Backend outage | health checks, rollback plan | `/health` not `200 OK` |
| Event endpoint failure | `/v1/events` gate | signed events not accepted |
| CORS failure | preflight validation | operator dashboard cannot observe |
| WebSocket failure | fallback requirement | ride tracking unavailable with no fallback |
| Wrong ride id | driver selected ride validation | hard-coded ride id detected |
| Replay failure | replay export gate | replay cannot reconstruct ride |
| Evidence gap | evidence bundle checklist | missing signed event log or receipt |
| Store rejection | compliance docs and claim discipline | required legal URL missing |
| Safety incident | emergency contact and incident log | unresolved live safety issue |
| Trust degradation | trust scoring and slashing | node behavior below pilot threshold |

## Claim Discipline

Use:

```text
controlled pilot
replay-governed coordination
protocol-backed evidence
```

Do not use:

```text
production-proven
guaranteed ride execution
immutable real-world truth
```
