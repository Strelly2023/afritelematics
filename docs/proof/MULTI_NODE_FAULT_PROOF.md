# Multi-Node Fault Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 2
CLASSIFICATION: DISTRIBUTED FAULT REPLAY EVIDENCE SURFACE
ROLE: PROVE REPLAY SURVIVABILITY UNDER DECLARED MULTI-NODE FAULTS
BOUNDARY: FAULT HARNESS DOES NOT DEFINE TRUTH; REPLAY AND RECOVERY VALIDATORS REMAIN AUTHORITY
```

This report documents Production Proof Gate 2.

The multi-node fault proof gate validates that declared distributed faults are
detected or canonically recovered without changing replay-valid execution.

## Required Faults

```text
worker crash
duplicate delivery
out-of-order queue
partition rebuild
node recovery
replay after failure
```

Each scenario must prove:

```text
fault detected or canonicalized
recovery succeeds
replay hash remains preserved
```

## Enforcement Surface

```text
afritech/distributed/testing/multi_node_fault_proof.py
afritech/tests/distributed/test_multi_node_faults.py
afritech/ci/multi_node_fault_validator.py
docs/proof/MULTI_NODE_FAULT_PROOF.md
```

The validator builds a replay-verified distributed baseline, injects declared
faults, applies deterministic recovery or canonicalization, and verifies that
post-fault replay returns to the baseline replay hash.

## Authority Boundary

Fault handling may recover execution.

It may not define truth.

The replay log, distributed replay verifier, partition recovery protocol, and
node recovery protocol remain the authority surfaces.

The fault proof gate only proves that declared multi-node failures do not
silently mutate replay-valid execution.

## Current Gate

```bash
python3 -m afritech.ci.multi_node_fault_validator
```

Passing this gate means AfriTech preserves deterministic constitutional replay
across the declared multi-node fault scenarios.
