# Observability Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 5
CLASSIFICATION: OBSERVABILITY EVIDENCE SURFACE
ROLE: PROVE SYSTEM STATE VISIBILITY WITHOUT GRANTING OBSERVABILITY AUTHORITY
BOUNDARY: OBSERVABILITY MAY REPORT SYSTEM STATE; REPLAY AND VALIDATORS REMAIN AUTHORITY
```

This report documents Production Proof Gate 5.

The observability proof validates that production visibility can report system
state and influence operations without becoming a truth source.

## Required Dashboard Evidence

```text
event count
partition lag
worker health
replay divergence count
recovery attempts
rejected executions
```

## Enforcement Surface

```text
afritech/observability/evidence.py
afritech/tests/observability/test_observability_evidence.py
afritech/ci/observability_evidence_validator.py
docs/proof/OBSERVABILITY_PROOF.md
```

Observability may report validator-derived and replay-derived system state.

Observability may influence operations by surfacing health, lag, divergence,
recovery, and rejection signals.

Observability may not define truth, override replay, ratify legitimacy, mutate
evidence, suppress failure, change validator results, or declare execution
admissible.

## Current Gate

```bash
python3 -m afritech.ci.observability_evidence_validator
```

Passing this gate means observability exposes the required production evidence
while preserving the authority boundary:

```text
Observability reports state.
Replay and validators define admissible truth.
```
