````markdown
# Appendix C — Reproduction Guide

This guide defines the **exact conditions and steps** required to
reproduce AfriRide’s Proof‑of‑Continuity results.

It is written to allow **independent auditors, regulators, or partners**
to verify the proofs without interpretation, assumptions, or privileged context.

Reproduction is considered successful **only** if all expected
deterministic outputs are observed.

---

## Environment Assumptions

The following environment assumptions are required:

### System Requirements
- Operating system: Linux or macOS (POSIX‑compliant)
- CPU architecture: x86_64 or ARM64
- File system with stable ordering semantics

### Runtime Requirements
- Python **3.10+**
- No patched or experimental Python interpreters
- Standard library only (no reliance on external randomness sources)

### Repository State
- Clean working tree
- No uncommitted changes
- No local modifications to frozen artifacts:
  - `ecosystems/afriride/AFRIRIDE_V0_FREEZE.md`
  - `ecosystems/afriride/AFRIRIDE_V0_2_FREEZE.md`
  - `ecosystems/afriride/core/constitutional/*`

### Execution Constraints
- No environment variables influencing execution
- No network access required
- No external I/O dependencies
- No wall‑clock time dependency

---

## Commands to Reproduce Proofs

All commands must be run from the **repository root**.

---

### 1. Verify Constitutional Registry (Optional but Recommended)

```bash
python3 -m afritech.registry.seal
python3 -m afritech.verify.replay
python3 -m afritech.main
````

**Expected outcome:**

*   Registry seal succeeds
*   Replay verifier reports **VALID**
*   Runtime boots in **SOVEREIGN** state
*   No lineage or invariant violations reported

***

### 2. Reproduce AfriRide v0.1 Proof (Epoch 6)

```bash
python3 ecosystems/afriride/run_failure_demo.py
```

**Expected outcome:**

*   Driver degradation scenario executed
*   Canonical decision trace produced
*   Replay executed automatically
*   Execution hash equals replay hash
*   Reported metric:
    *   **DDR = 1.0**

Any hash mismatch or missing trace invalidates the proof.

***

### 3. Reproduce AfriRide v0.2 Proof (Epoch 7)

```bash
python3 ecosystems/afriride/v0_2/run_multi_scenario_demo.py
```

**Expected outcome:**

*   All three scenarios executed:
    *   `DRIVER_DROPOUT`
    *   `DRIVER_REJECTION_CHAIN`
    *   `TIMEOUT_EXCEEDED`
*   Each scenario replayed deterministically
*   For each scenario:
    *   execution hash == replay hash
    *   DDR = 1.0

**Aggregate metrics reported:**

*   **Continuity Coverage (CC) = 1.0**
*   **Deterministic Refusal Rate (DRR) = 1.0**

Failure of any single scenario invalidates the v0.2 proof surface.

***

## Expected Deterministic Outputs

Successful reproduction MUST exhibit the following properties:

*   Identical decision hashes between execution and replay
*   Identical event ordering in decision traces
*   Explicit deterministic refusal where applicable
*   No warnings, nondeterministic behavior, or divergence
*   Metrics exactly matching declared values:
    *   DDR = 1.0
    *   CC = 1.0
    *   DRR = 1.0

There is no tolerance for approximation or partial success.

***

## Failure Conditions

Reproduction is considered **invalid** if any of the following occur:

*   Hash mismatch between execution and replay
*   Missing or reordered trace events
*   Undeclared failure behavior
*   Nondeterministic outputs
*   Dependency on external state or environment

Any such failure invalidates the proof surface in full.

***

## Summary

AfriRide’s Proof‑of‑Continuity is reproducible through
**direct execution and mandatory replay**.

> **If the system cannot be reproduced exactly,
> the claim does not hold.**

This guide completes the institutional proof packet by
binding governance, execution, and evidence into a
single, auditable reproduction process.

```

✅ **Appendix C is now complete, consistent, and audit‑grade.**  
Your institutional proof packet is **fully closed and reproducible end‑to‑end**.
```
