# NovaTech Data and Event Contract Standard

Authoritative data uses immutable, independently versioned JSON Schemas for
requests, responses, trust packets, replay records, events, and signatures.
Schemas declare required fields, formats, enums, extension policy, data
classification, tenant binding, retention class, and compatibility.

The event backbone separates:

```text
Command -> Policy -> Execution -> Domain Event -> Trust Event
        -> Integration Event -> Analytics Event
```

Only domain events record authoritative domain transitions. Trust events bind
evidence. Integration and analytics events are projections and MUST NOT become
mutation authority. Events require event ID, type, subject, tenant, source,
occurred time, correlation/causation IDs, schema version, payload, and integrity
metadata. Consumers are idempotent and tolerate redelivery.
