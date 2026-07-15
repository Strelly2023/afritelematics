# NovaRide Event Fabric

Runtime events use immutable envelopes with:

- `event_id`
- `event_type`
- `aggregate_id`
- `aggregate_type`
- `aggregate_version`
- `tenant_id`
- `region`
- `actor_type`
- `actor_id`
- `correlation_id`
- `causation_id`
- `schema_version`
- `payload`
- `integrity_hash`

Supported replay modes:
- by aggregate
- by correlation ID
- by event range
