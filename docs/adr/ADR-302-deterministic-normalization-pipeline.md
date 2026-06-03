# ADR-302: Deterministic Normalization Pipeline

STATUS: IMPLEMENTED EVIDENCE SLICE

## Decision

AfriRide normalizes noisy external observations into a closed deterministic
event stream before execution admission.

The pipeline is:

```text
observation validation
-> authority field rejection
-> canonical payload hashing
-> timestamp authority bucketing
-> optional GPS cell quantization
-> duplicate collapse or rejection
-> deterministic ordering
-> normalized event id emission
-> normalized event admission validation
-> ingestion trace stamping
```

## Pipeline Contract

For identical multisets of raw observations:

```text
normalize(A) == normalize(permutation(A))
```

For duplicate observations:

```text
same source_id + event_id + same normalized content -> one event
same source_id + event_id + different normalized content -> rejection
```

For hostile authority fields:

```text
replay_hash | replay_id | witness_hash | mutation_witness | constitutional_authority
-> rejection before admission
```

For tampered normalized events:

```text
normalized_event_id != hash(normalized content + sequence)
-> rejection before ingestion
```

## Evidence

The validator `afritech.ci.normalization_validator` emits a replay-safe
validation receipt containing:

```text
normalized_event_trace
normalized_event_admission_trace
clock_drift_normalization_receipt
duplicate_delivery_rejection_trace
replay_injection_rejection_trace
tampered_normalized_event_rejection_trace
```

## Non-Claims

This ADR does not make normalized events operationally true. It makes them
admissible candidates for later admission, execution, witness, and replay
surfaces.
