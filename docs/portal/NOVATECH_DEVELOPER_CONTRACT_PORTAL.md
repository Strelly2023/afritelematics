# NovaTech Developer Contract Portal

The contract portal is exposed at `GET /v1/core-platform/contracts`.

It provides:

- the current machine-readable platform contract;
- signed schema publications and SHA-256 digests;
- request, response, event, trust, replay, and signature schemas;
- the capability dependency graph;
- architectural compliance metrics;
- version-vector negotiation;
- federation compatibility metadata;
- Python, TypeScript, Kotlin, and Swift SDK contract artifacts.

## API explorer

Use `GET /v1/core-platform/contracts/schemas/{schema_name}` to retrieve a live
schema and its signed publication metadata. Supported names are `request`,
`response`, `event`, `trust`, `replay`, and `signature`.

Use `POST /v1/core-platform/contracts/validate` with:

```json
{
  "schema_name": "request",
  "payload": {}
}
```

The endpoint returns HTTP 422 when the payload violates the canonical schema.

## Version negotiation

Clients may send:

```text
Accept-Contract-Version: 2.0.0
Accept-Replay-Version: 1.0.0
Accept-Evidence-Version: 1.0.0
Accept-Signature-Version: 1.0.0
```

`GET /v1/core-platform/contracts/negotiate` returns `COMPATIBLE` or HTTP 426
with negotiation details. Federation nodes publish the same dimensions at
`GET /v1/core-platform/federation/manifest`.

## SDK artifacts

Generated language contracts live under `docs/sdk/generated`. They contain the
same version vector and governed envelope vocabulary. SDK artifacts do not
replace runtime schema validation; they provide typed client ergonomics around
the authoritative schemas.

Regenerate them with:

```bash
python -m afritech.platform_contracts.sdk_generator \
  --output-dir docs/sdk/generated
```
