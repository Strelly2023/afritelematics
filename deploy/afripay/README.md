# AfriPay Deployment Pack

This deployment pack runs the AfriPay GA Elite core with live settlement disabled by default.

## Local Compose

```bash
docker compose -f deploy/afripay/docker-compose.afripay.yml up --build
```

## Kubernetes

```bash
kubectl apply -f deploy/afripay/kubernetes/namespace.yaml
kubectl apply -f deploy/afripay/kubernetes/secret.example.yaml
kubectl apply -f deploy/afripay/kubernetes/
```

Replace `secret.example.yaml` before any shared environment. Do not enable
`AFRIPAY_LIVE_SETTLEMENT_ENABLED` without a compliance activation reference,
provider credentials, treasury controls, and operational approval.

## Async Workers

The worker runs:

```bash
celery -A afritech.afripay.celery_app:app worker --loglevel=INFO --queues=afripay
```

Redis is used as broker and result backend in local and Kubernetes examples.

## Security and monitoring

- OAuth token issuance uses `AFRIPAY_OAUTH_SECRET`
- API metrics are exposed at `/api/afripay/metrics/prometheus`
- Webhooks can be protected with `AFRIPAY_WEBHOOK_SECRET` or provider-specific secrets
- Sandbox provider mode is enabled with `AFRIPAY_PROVIDER_MODE=sandbox`
- Prometheus runs on `:9090` and Grafana on `:3000` in the compose stack
