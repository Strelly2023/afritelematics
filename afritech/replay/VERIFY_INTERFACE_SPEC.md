Below is the **complete canonical version** of:

# `afritech/replay/VERIFY_INTERFACE_SPEC.md`

This formally closes the implementation ambiguity boundary between:

* `REPLAY_VERIFIER_SPEC.md`
* `verify.py`

and defines the exact deterministic runtime contract for replay verification.

---

````md id="7ibcfi"
# VERIFY INTERFACE SPECIFICATION
## File
`afritech/replay/VERIFY_INTERFACE_SPEC.md`

---

## Status
**IMPLEMENTATION CONTRACT ARTIFACT**

---

## Authority

Derived exclusively from:

- `afritech/replay/REPLAY_VERIFIER_SPEC.md`
- `afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md`
- constitutional registry continuity

This specification defines the exact runtime interface contract for:

`afritech/replay/verify.py`

No implementation may deviate from this contract.

---

# Constitutional Constraint

Implementation ambiguity is constitutionally prohibited.

The replay verifier implementation MUST conform exactly to the interface
defined herein.

Any deviation invalidates replay legitimacy.

---

# 1. PURPOSE

This specification exists to:

1. eliminate implementation ambiguity
2. define deterministic verifier invocation
3. constrain replay verdict semantics
4. formalize failure emission
5. preserve constitutional replay law

It bridges:

**replay law**

and

**runtime execution**

---

# 2. CANONICAL MODULE

The verifier implementation SHALL exist exclusively at:

```plaintext id="8k6udm"
afritech/replay/verify.py
````

No alternate replay verifier implementation is permitted.

---

# 3. REQUIRED PUBLIC INTERFACE

The verifier MUST expose exactly one public verification entry point.

---

## Canonical interface

```python id="w2yngt"
class ReplayVerifier:
    def verify(
        self,
        transcript_path: str,
        request: ConstitutionalRequest
    ) -> ReplayVerdict:
        ...
```

---

## Interface invariants

The method MUST:

* be deterministic
* be side-effect free
* return synchronously
* emit explicit verdict

The method MUST NOT:

* mutate transcript
* mutate request
* perform external writes
* modify registry state

---

# 4. INPUT CONTRACT

---

## 4.1 transcript_path

Type:

```python id="rr2eqy"
str
```

---

### Constraints

Must reference canonical transcript file.

Must resolve to:

* readable
* immutable
* schema-valid transcript

---

### Failure mode

```yaml id="mjlwmq"
invalid_transcript_path
```

---

## 4.2 request

Type:

```python id="l26j7g"
ConstitutionalRequest
```

---

### Constraints

Request MUST:

* conform to constitutional request schema
* hash-identically match transcript request_hash

---

### Failure mode

```yaml id="6w2t3g"
request_mismatch
```

---

# 5. OUTPUT CONTRACT

Verifier MUST return:

```python id="ybm3o0"
ReplayVerdict
```

---

## Canonical structure

```python id="x3x2gr"
class ReplayVerdict:
    status: str
    replay_hash: str | None
    failure_mode: str | None
    environment_match: bool
    trace_match: bool
    truthpacket_match: bool
    violated_invariant: str | None
    divergence_location: str | None
```

---

# 6. VERDICT STATUS LAW

Only two statuses are permitted.

---

## Valid success

```python id="9ec42e"
REPLAY_VALID
```

---

## Valid failure

```python id="cllfwl"
REPLAY_INVALID
```

---

## Prohibition

Intermediate or probabilistic verdicts are forbidden.

Forbidden examples:

* PARTIAL_VALID
* LIKELY_VALID
* MOSTLY_VALID

These violate constitutional replay law.

---

# 7. VERIFICATION EXECUTION ORDER

Implementation MUST execute exactly in this order.

No reordering permitted.

---

## Canonical sequence

```text id="s54s1h"
1. load_transcript
2. validate_environment
3. reconstruct_request
4. rerun_execution
5. regenerate_truthpacket
6. recompute_hashes
7. compare_results
8. emit_verdict
```

---

## Ordering invariant

Later stages MUST NOT influence earlier validation.

---

# 8. DETERMINISTIC HASHING CONTRACT

Replay determinism depends on exact hashing law.

---

## Required algorithm

```plaintext id="q8s0mh"
SHA-256
```

---

## Encoding

```plaintext id="3ch9bq"
UTF-8
```

---

## Serialization rules

All replay artifacts MUST be serialized with:

* stable key ordering
* normalized whitespace
* canonical newline format
* deterministic field ordering

---

## Prohibited variability

Forbidden:

* platform-dependent ordering
* unordered dict serialization
* locale-sensitive encoding
* timestamp injection

---

# 9. FAILURE EMISSION CONTRACT

All failures MUST emit explicit structured failure.

---

## Canonical failure structure

```python id="i9znh0"
class ReplayFailure:
    failure_mode: str
    violated_invariant: str
    divergence_location: str
    details: str
```

---

## Mandatory emission

ReplayVerifier MUST emit ReplayFailure before returning:

```python id="tmbm8g"
REPLAY_INVALID
```

---

# 10. CANONICAL FAILURE MODES

Permitted failure classifications:

```yaml id="0o7v3e"
failure_modes:
  - invalid_transcript_path
  - invalid_transcript_schema
  - request_mismatch
  - environment_mismatch
  - trace_divergence
  - truthpacket_divergence
  - hash_mismatch
  - nondeterministic_execution
  - incomplete_transcript
  - constitutional_scope_mismatch
```

No additional runtime-defined failures permitted.

---

# 11. DIVERGENCE LOCATION LAW

If replay fails, implementation MUST identify exact divergence location.

Permitted values:

```yaml id="hkt8e2"
divergence_location:
  - transcript_load
  - environment_validation
  - request_reconstruction
  - execution_rerun
  - truthpacket_regeneration
  - hash_recomputation
  - verdict_comparison
```

---

# 12. SIDE-EFFECT PROHIBITION

Replay verification MUST be observational only.

Verifier MUST NOT:

* mutate files
* alter registry
* advance epoch
* write network state
* emit external actions

Violation invalidates verifier legitimacy.

---

# 13. DETERMINISM REQUIREMENT

Multiple invocations of:

```python id="vzzx2w"
ReplayVerifier.verify()
```

under identical inputs MUST return identical:

* status
* replay_hash
* failure classification
* divergence location

---

# 14. EXCEPTION HANDLING LAW

Unstructured exceptions are constitutionally forbidden.

Implementation MUST convert all runtime exceptions into:

```python id="hwnwio"
ReplayFailure
```

before verdict emission.

---

# 15. SUCCESS CONTRACT

ReplayVerifier may emit:

```python id="c4llxm"
REPLAY_VALID
```

only if ALL conditions hold:

* transcript loaded
* environment matched
* request reconstructed
* execution rerun
* TruthPacket regenerated
* hashes matched
* trace matched
* no divergence detected

---

# 16. INVALIDATION CONDITIONS

ReplayVerifier MUST emit:

```python id="c7tygc"
REPLAY_INVALID
```

if ANY condition fails.

No partial validity permitted.

---

# 17. TESTABILITY REQUIREMENT

Implementation MUST support deterministic unit testing.

Required test surfaces:

```plaintext id="q3ffr0"
afritech/tests/replay/
```

Minimum tests:

* valid replay
* hash mismatch
* trace divergence
* environment mismatch
* malformed transcript
* nondeterministic rerun

---

# 18. PROOF BOUNDARY DECLARATION

Conformance to this interface establishes:

✅ implementation contract compliance

It does NOT establish:

❌ replay validity
❌ constitutional execution proof
❌ operational legitimacy

Those require successful runtime execution.

---

# 19. CONSTITUTIONAL ASSERTION

The verifier interface exists to ensure:

**implementation cannot weaken replay law.**

Code must obey specification.

Specification does not adapt to code.

---

# 20. FINAL IMPLEMENTATION GATE

`afritech/replay/verify.py`
may be considered constitutionally valid only if:

1. it conforms exactly to this interface
2. it passes deterministic replay tests
3. it emits lawful verdicts

Only then may it participate in constitutional proof.

No weaker implementation is permitted.

```

---

This is the complete canonical version of:

**`afritech/replay/VERIFY_INTERFACE_SPEC.md`**

With this, AfriTech now has a complete replay stack documentation chain:

- execution proof law
- replay verification law
- verifier implementation contract

The next lawful step is actual implementation of:

`afritech/replay/verify.py`
```
