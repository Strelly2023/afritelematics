# Production route ownership

The aggregate FastAPI application must register each HTTP method and normalized
path exactly once. Compatibility aliases may remain available when a router is
used independently, but the production aggregate disables aliases owned by a
different canonical router.

| Surface | Canonical production owner | Conflict resolution |
| --- | --- | --- |
| Driver availability and ride queue | `afritech.api.afriride_next_gen_mobile_api` | NovaRide runtime exposes its service-specific variants only below `/v1/novaride/runtime/driver/...`. |
| Platform products | `afritech.api.platform_runtime_api` | Data governance keeps `/v1/novatech/data-governance/...`; its legacy `/v1/platform/...` aliases are disabled only in the aggregate app. |
| Platform migration catalogue | `afritech.api.api_catalog` | Data-governance migration aliases are disabled only in the aggregate app. |
| NovaCodePro authentication/session endpoints | `afritech.api.novacodepro_platform_api` | The duplicate dedicated session router is not mounted in the aggregate app. Shared session logic remains reusable. |

`afritech/tests/api/test_production_route_uniqueness.py` inspects the actual
mounted application and fails for duplicate method/path registrations, missing
OpenAPI operation IDs, duplicate operation IDs, or FastAPI duplicate-operation
warnings.
