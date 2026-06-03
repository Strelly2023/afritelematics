# Mobile Event Contract

STATUS: CANONICAL PILOT CONTRACT
CLASSIFICATION: MOBILE TO EDGE INGESTION BOUNDARY

## Canonical Schemas

```text
afritech/api/contracts/event.schema.json
afritech/api/contracts/event_batch.schema.json
```

## Runtime Validators

```text
afritech.api.contracts.validator.EventContractValidator
afritech.api.contracts.rules.EventContractRules
afritech.api.ingestion.event_ingestion.EventIngestionAPI
```

## Required Guarantees

```text
Event schema must be valid JSON schema
No extra fields allowed
logical_clock strictly increasing per device
event_id globally unique within ingestion window
payload must be structured JSON
signature must validate event integrity
invalid inputs are rejected deterministically
```

## Forbidden

```text
direct state mutation via API
missing signature
unordered logical clocks
mutable event content after submission
silent correction of invalid events
runtime witness claims from clients
replay authority fields from clients
```

## Ingestion Order

```text
schema validation
-> signature verification
-> duplicate check
-> logical clock rule
-> forbidden authority field check
-> normalization handoff
```

## Non-Claims

This contract does not claim production deployment, public launch readiness,
payment finality, KYC completion, or completed pilot validation.
