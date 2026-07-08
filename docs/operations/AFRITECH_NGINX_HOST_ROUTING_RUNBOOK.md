# AfriTechnology NGINX Host Routing Runbook

This runbook documents the production-safe host-based routing pattern for the
AfriTechnology platform when all subdomains terminate on a single EC2 host.

## Routing Topology

- `afritechnology.com` and `www.afritechnology.com` -> dashboard / main website
- `app.afritechnology.com` -> application portal
- `api.afritechnology.com` -> FastAPI backend
- `verify.afritechnology.com` -> verification portal/API
- `identity.afritechnology.com` -> NovaID portal
- `trust.afritechnology.com` -> NovaTrust portal
- `merchant.afritechnology.com` -> NovaPay merchant portal
- `business.afritechnology.com` -> NovaPay business portal
- `agent.afritechnology.com` -> NovaPay agent portal
- `fleet.afritechnology.com` -> NovaRide fleet portal
- `operator.afritechnology.com` -> NovaRide operations portal
- `support.afritechnology.com` -> support center
- `status.afritechnology.com` -> status dashboard
- `developer.afritechnology.com`, `docs.afritechnology.com`, `download.afritechnology.com` -> developer portal

## Port Map

- `3000` main website / dashboard
- `3001` API gateway / FastAPI
- `4001` NovaID Portal
- `4002` NovaTrust Portal
- `4003` Merchant Portal
- `4004` Business Portal
- `4005` Operator Console
- `4006` Agent Portal
- `4007` Fleet Management
- `4008` Support Center
- `4009` Status Dashboard
- `4010` Developer Portal

## Safety Notes

- This routing file is only valid if the upstream services are already listening
  on the documented localhost ports.
- If the upstream process is absent, NGINX will return `502 Bad Gateway`.
- `app.afritechnology.com` remains the default landing surface for unmatched
  requests via the fallback server block.

