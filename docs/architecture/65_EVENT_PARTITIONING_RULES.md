# NovaRide Event Partitioning Rules

Status: CANONICAL STREAM PARTITION POLICY
Classification: ORDERING AND SCALING SURFACE

## Goal

Preserve ordering where it matters while allowing horizontal scaling.

## Partition Keys

- ride lifecycle events: `ride_id`
- trip execution events: `trip_id`
- dispatch assignment events: `ride_id`
- driver presence events: `driver_id`
- payment events: `payment_id` or `ride_id`
- wallet events: `wallet_id`
- policy decisions: `decision_id`
- approvals: `approval_id`
- inspections: `inspection_id`
- support tickets: `ticket_id`
- verification events: `verification_id`

## Rules

- one aggregate must map to one ordering domain
- never partition by random UUID if ordering is required
- never partition sensitive control events across unrelated keys
- public verification projections may use derived keys

