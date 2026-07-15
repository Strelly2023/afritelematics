# NovaRide Production Operations Guide

This guide covers the operated resilience platform: provider probes, circuit breakers, mobile sync, outbox publishing, failover evaluation, SLOs, and readiness evidence.

Safe commands:

```bash
pytest tests/novaride_runtime/unit tests/novaride_runtime/contracts tests/novaride_runtime/deployment
python scripts/novaride/run_dr_exercise.py --exercise emergency-path-verification --environment controlled_pilot --region KE
python scripts/novaride/validate_production_readiness.py reports/novaride/readiness/latest.json
kubectl apply -k deploy/novaride/production
```

Do not run destructive DR exercises in production without explicit authorization.

Core APIs:

- `GET /v1/novaride/operations/resilience/status`
- `GET /v1/novaride/operations/providers`
- `GET /v1/novaride/operations/circuits`
- `GET /v1/novaride/operations/offline-queues`
- `GET /v1/novaride/operations/sync/conflicts`
- `GET /v1/novaride/operations/slo`
- `GET /v1/novaride/operations/readiness-certificate`

Evidence closure requires immutable evidence hashes, operator reason, approval reference for high-risk commands, and the relevant runbook checklist.
