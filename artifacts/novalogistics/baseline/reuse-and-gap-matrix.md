# NovaLogistics reuse and gap matrix

| Capability | Classification | Evidence / note |
|---|---|---|
| Custody chain and proof | EXISTING_COMPLETE | `afritech.mobility.logistics_custody_chain` and passing tests |
| Public product page | EXISTING_COMPLETE | `apps/public-web/src/novalogistics.jsx` and 5 passing tests |
| Settlement boundary | SHARED_PLATFORM_REUSE | `afritech.mobility.settlement_boundary`; NovaPay remains authority |
| Geographic point | SHARED_PLATFORM_REUSE | `ecosystems.afriride.geo.types.GeoPoint` |
| Core logistics domain types | EXISTING_STUB | `afritech.novaride_runtime.logistics` contains only a package marker |
| Shipment/order lifecycle | MISSING | NL-001 scope |
| Durable aggregate persistence/outbox | MISSING | NL-002 scope |
| Authentication/RBAC/tenant policy | EXISTING_PARTIAL | Shared platform capabilities exist; logistics integration absent |
| Customer booking/tracking | MISSING | NL-004 scope |
| Driver execution | EXISTING_PARTIAL | NovaRide driver surfaces exist; logistics workflows incomplete |
| Fleet management | EXISTING_PARTIAL | Fleet apps/domain modules exist; NovaLogistics contracts incomplete |
| Warehouse management | MISSING | No canonical WMS domain found |
| Transportation management | EXISTING_PARTIAL | Dispatch/routing assets exist; full TMS absent |
| Last-mile platform | EXISTING_PARTIAL | NovaRide and Africonnect assets reusable |
| Freight marketplace | MISSING | NL-010 scope |
| NovaID integration | BLOCKED_EXTERNAL_INTEGRATION | Contracts can be built; live credential validation needs provider evidence |
| NovaPay integration | EXISTING_PARTIAL | Shared settlement/payment contracts exist; logistics adapter absent |
| AI/optimization | EXISTING_PARTIAL | Shared intelligence hooks exist; capability-specific contracts absent |
| Workflow automation | MISSING | NL-014 scope |
| Analytics/reporting | EXISTING_PARTIAL | Shared dashboards exist; trusted logistics read models absent |
| Enterprise integration gateway | EXISTING_PARTIAL | Public/API infrastructure reusable |
| Operational portals | EXISTING_PARTIAL | Several NovaRide portals exist; role-complete workflows absent |
| Mobile hardening | EXISTING_PARTIAL | Driver/fleet apps exist; certification evidence absent |
| Cloud/security/reliability | EXISTING_PARTIAL | Shared deployment controls exist; NovaLogistics evidence absent |
| Compliance/governance | EXISTING_PARTIAL | Shared controls exist; logistics-specific workflows incomplete |
| Industry packs | MISSING | NL-022 scope |
| Enterprise services | MISSING | NL-023 scope |
| End-to-end validation | MISSING | NL-024 scope |
| Release certification | MISSING | NL-025 scope |
