# NovaRide Event Topic Model

Status: CANONICAL STREAM TOPOLOGY
Classification: EVENT ROUTING SURFACE

## Topic Strategy

Topics are organized by business domain and replay sensitivity.

## Recommended Topic Groups

### Core mobility topics

- `novaride.ride`
- `novaride.trip`
- `novaride.dispatch`
- `novaride.driver`

### Payments topics

- `novaride.payment`
- `novaride.wallet`
- `novaride.transaction`

### Control-plane topics

- `novaride.policy`
- `novaride.approval`
- `novaride.feature_flag`
- `novaride.workflow`

### Trust and evidence topics

- `novaride.trust`
- `novaride.compliance`
- `novaride.audit`
- `novaride.replay`
- `novaride.verification`

### Operations and support topics

- `novaride.support`
- `novaride.notification`
- `novaride.inspection`
- `novaride.analytics`

## Topic Rules

- one topic family per bounded context
- use partition key for aggregate ordering
- keep control-plane topics separate from execution topics when possible
- keep public verification reads isolated from internal topics

## Partition Guidance

- ride and trip events partition by `trip_id` or `ride_id`
- driver events partition by `driver_id`
- payment events partition by `payment_id` or `ride_id`
- policy and approval events partition by `decision_id`
- audit events partition by `tenant_id` or `correlation_id`

## Retention Guidance

- operational execution topics: medium retention
- audit and replay topics: long retention
- public verification projections: derived, not authoritative

