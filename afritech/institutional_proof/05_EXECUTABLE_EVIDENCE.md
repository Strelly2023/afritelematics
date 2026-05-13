````markdown
# Executable Evidence

AfriRide’s claims are supported exclusively by **runnable, deterministic programs**.
There are no diagrams, simulations, or illustrative examples.
Correctness is demonstrated only through **execution and replay**.

This section defines **exactly what to run**, **what must be observed**, and
**how validity is determined**.

---

## AfriRide v0.1 — Baseline Proof (Epoch 6)

### Command

```bash
python3 ecosystems/afriride/run_failure_demo.py
````

### What This Executes

*   Deterministic coordination under a single degraded‑input scenario
*   Canonical decision trace construction
*   Replay of the same execution
*   Hash comparison between execution and replay

### Expected Outcome

*   identical execution and replay decision hashes
*   explicit decision trace produced
*   deterministic refusal or assignment as declared
*   **Decision Determinism Rate (DDR) = 1.0**

Any replay mismatch invalidates the proof.

***

## AfriRide v0.2 — Multi‑Scenario Proof (Epoch 7)

### Command

```bash
python3 ecosystems/afriride/v0_2/run_multi_scenario_demo.py
```

### What This Executes

*   Deterministic execution of all declared v0.2 scenarios:
    *   `DRIVER_DROPOUT`
    *   `DRIVER_REJECTION_CHAIN`
    *   `TIMEOUT_EXCEEDED`
*   Replay of each scenario under identical conditions
*   Metric computation across the bounded failure space

### Expected Outcome (All Scenarios)

*   identical execution and replay decision hashes
*   deterministic refusal where applicable
*   no undeclared behavior paths
*   no nondeterministic variation

### Required Metrics

*   **Decision Determinism Rate (DDR): 1.0** (per scenario)
*   **Continuity Coverage (CC): 1.0**
*   **Deterministic Refusal Rate (DRR): 1.0**

Failure of any single scenario invalidates the v0.2 proof surface.

***

## Validity Rule

Executable evidence is considered valid **only if**:

    hash(original_execution) == hash(replay_execution)

This condition must hold for:

*   every scenario
*   every execution
*   every replay

There is no partial acceptance condition.

***

## Summary

AfriRide’s correctness is demonstrated through:

*   direct execution
*   canonical trace generation
*   mandatory replay
*   exact hash equivalence

If the code does not replay identically, **the claim does not hold**.

This makes AfriRide’s guarantees:

*   executable
*   auditable
*   reproducible
*   institution‑grade

```

✅ This file is now **complete**, **audit‑ready**, and **aligned with all frozen guarantees**.

If you want to continue, the next natural section is:

👉 **06_LIMITS_AND_NON_CLAIMS.md**
```
