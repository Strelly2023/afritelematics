# ADR-301: Edge Adapter Normalization Boundary

STATUS: IMPLEMENTED EVIDENCE SLICE

## Decision

AfriRide admits real-world inputs only as raw edge observations until they pass
through deterministic normalization.

The boundary is:

```text
raw reality
-> adapter-shaped observation
-> deterministic normalization
-> queue-mediated admission
```

## Authority Rule

Client clocks, GPS readings, provider payloads, and public API bodies are
observational. They are never runtime truth, replay authority, witness authority,
or mutation authority.

Ordering authority is the ingress-controlled receipt time carried by the edge
observation as `received_at_ms`.

## Implemented Surface

```text
afritech.edge.normalization.reality_events
afritech.edge.ingestion.reality_ingestor
afritech.ci.normalization_validator
afritech.tests.governance.test_reality_event_normalization
```

## Proven In This Slice

```text
unordered inputs converge
duplicate identical observations collapse
conflicting duplicates fail closed
GPS coordinates are range-checked and quantized
client time is retained only as observational evidence
replay/witness authority injection is rejected
normalized traces receive deterministic event ids
tampered normalized event ids are rejected before ingestion
admitted traces carry adapter -> normalization -> ingestion evidence
```

## Non-Claims

This ADR does not claim production deployment, full GPS fraud detection, payment
finality, provider trust, complete mobile sync, or complete state-space
exhaustiveness.

It proves only that the normalization boundary now has an executable,
replay-stable evidence slice for noisy real-world observations.
