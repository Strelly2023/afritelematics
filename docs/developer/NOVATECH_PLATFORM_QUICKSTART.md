# NovaTech Platform Quickstart

1. Inspect contracts with `GET /v1/core-platform/contracts`.
2. Negotiate versions with `GET /v1/core-platform/contracts/negotiate`.
3. Validate locally with:

```bash
python -m afritech.ci.novatech_platform_contract_validator
```

4. Generate SDK contracts with:

```bash
python -m afritech.platform_contracts.sdk_generator \
  --output-dir /tmp/novatech-sdk
```

5. Submit a governed request to `POST /v1/core-platform/contracts/admit`.
6. Inspect operational gates at `GET /v1/core-platform/operations/readiness`.

The request tenant and actor must match authenticated claims. Contract,
evidence, replay, and signature versions must negotiate successfully before
execution.
