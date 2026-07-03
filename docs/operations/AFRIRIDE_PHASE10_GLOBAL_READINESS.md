# Phase 10 — Global Readiness

## Global contract

`afriride.global.v1` is the bootstrap contract for region, locale, currency,
time zone, compliance, pricing, and tenant branding. Initial policies cover:

| Region | Country | Currency | Time zone | Locales |
|---|---|---|---|---|
| `au-mel` | Australia | AUD | Australia/Melbourne | en-AU |
| `ug-kla` | Uganda | UGX | Africa/Kampala | en-UG, sw-UG |
| `ke-nbo` | Kenya | KES | Africa/Nairobi | en-KE, sw-KE |
| `ng-los` | Nigeria | NGN | Africa/Lagos | en-NG |
| `za-jnb` | South Africa | ZAR | Africa/Johannesburg | en-ZA, zu-ZA |

All persisted instants remain UTC. APIs return both UTC and IANA-zone local
representations where local operational time is relevant.

## Dispatch and pricing

Dispatch requests carry `region_id`. Drivers outside that region or failing the
country compliance gate are excluded before weighted ranking. Existing weighted
factors and dispatch authority remain unchanged.

Pricing uses versioned regional rules for base fare, distance, duration, minimum
fare, booking fee, surge cap, vehicle multiplier, tax, currency, and minor-unit
digits. `POST /v1/global/pricing/quote` remains the authoritative quote calculation.

## Localization and white label

Both apps load `/v1/global/config`, cache it for offline startup, and use locale-aware
money and time formatting. English, Swahili, and isiZulu navigation catalogs are
included. Tenant overrides can set brand name, primary color, logo URL, support URL,
and enabled regions without forking either application.

Configure tenant overlays through `AFRIRIDE_TENANT_CONFIG_JSON`:

```json
{
  "fleet-a": {
    "regions": ["ke-nbo"],
    "brand": {
      "name": "Safari Fleet",
      "short_name": "Safari",
      "primary_color": "#112233",
      "logo_url": "https://cdn.example.com/safari.png"
    }
  }
}
```

Mobile release variables:

```text
EXPO_PUBLIC_AFRIRIDE_REGION_ID=ke-nbo
EXPO_PUBLIC_AFRIRIDE_LOCALE=sw-KE
EXPO_PUBLIC_AFRIRIDE_ORGANIZATION_ID=fleet-a
```

## Compliance operations

`POST /v1/global/compliance/check` evaluates country-specific driver documents and
returns missing evidence, dispatch eligibility, and policy references. Legal and
operations owners must version policies when requirements change; application code
must not embed regulatory decisions outside this registry.

## Multi-region deployment

Run regional API, Redis, worker, and database cells close to each operating market.
Route by `region_id`, keep actor/ride affinity within a cell, replicate only approved
global reference data, and respect the region's `data_residency` policy. Global
operations should consume redacted metrics rather than raw trip or identity records.
