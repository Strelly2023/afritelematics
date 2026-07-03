# NovaRide App Store

## Purpose

The NovaRide App Store is the governed distribution surface for the NovaRide
ecosystem. It discovers apps, validates app manifests, stages sandbox
installs, and publishes approved listings.

All publishing remains policy-gated. NovaPower owns execution approval and
NovaTrust owns verification.

## API Surface

- `GET /v1/novaride/appstore/apps`
- `POST /v1/novaride/appstore/install`
- `POST /v1/novaride/appstore/publish`
- `GET /v1/architecture/app-store`

## Revenue Model

- app sales
- subscriptions
- transaction fees
- API usage
- NVT-backed ecosystem payments

## Governing Rules

- App manifests SHALL be versioned.
- App permissions SHALL be explicit.
- Sandbox execution SHALL occur before publish.
- Contract compatibility SHALL be validated.
- Security scans SHALL run before listing approval.

## Publishing Flow

1. Developer submits manifest.
2. Security and contract checks run.
3. Sandbox validation executes.
4. Policy review approves or rejects the listing.
5. The app is published to the governed catalog.
