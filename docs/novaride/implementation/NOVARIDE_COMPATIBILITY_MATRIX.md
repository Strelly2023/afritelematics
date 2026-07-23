# NovaRide compatibility matrix

| Surface | Public contract to preserve | Current implementation | Compatibility action |
|---|---|---|---|
| Rider Android | Existing deep links, auth/session and ride lifecycle | `rider_app` | Additive changes; retain release-channel guards |
| Driver Android | Availability, offer and trip transition contracts | `driver_app` | Additive changes; preserve offline command semantics |
| Fleet mobile | Fleet, driver and vehicle identifiers | `novaride_fleet_app` | Preserve identifiers and tenant scoping |
| Operator mobile | Driver/operator role routes | `novaride_operator_app` | Preserve existing role split and audit events |
| Runtime API | Existing `/v1` mobility routes and schemas | `afritech/api/novaride_runtime_api.py` | Version breaking changes; add contract tests |
| Operations web | Existing public route and role controls | `apps/novaride-operations` | Preserve routes; replace prototype data behind adapters |
| Admin web | Existing admin route and actions | `apps/novaride-admin` | Require privileged-action audit and approval |
| Corporate web | Existing tenant contracts | `apps/novaride-corporate` | Enforce tenant/region row filtering |
| Events | Existing envelope, event names and schema versions | `afritech/novaride_runtime/events` | Apply backward-compatible schema evolution |
| Database | Migrations `0001` through `0008` | PostgreSQL migration directory | Forward-only additive migrations with rollback procedure |
| Release downloads | Existing versioned APK URLs/checksums | `apk-public` and release manifests | Never replace immutable binaries in place |

## Compatibility gates

- Contract and OpenAPI comparison for API changes.
- Event schema backward-compatibility checks.
- Upgrade and clean migration tests.
- Deep-link and session migration tests.
- Release URL, checksum and artifact provenance tests.
- Explicit deprecation window for removed behavior.
