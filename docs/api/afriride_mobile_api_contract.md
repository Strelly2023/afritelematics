# AfriRide Mobile API Contract

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `DELETE /account`

## Ride Lifecycle

- `POST /rides/request`
- `POST /rides/accept`
- `POST /rides/start`
- `POST /rides/complete`
- `GET /rides/:id`

## Protocol Evidence

- `GET /proof/:ride_id`
- `GET /replay/:ride_id/status`
- `GET /ledger/:ride_id`
- `GET /state/ride/:id`

## Internal

- `GET /trust/node/:id`

## Support

- `POST /support/ticket`

## Contract Rule

Mobile apps are interface-only. Pricing, dispatch, proof finalization, replay, trust, and ledger authority remain server/protocol owned.
