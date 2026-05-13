# Audit Checklist

This checklist defines the **minimum constitutional conditions** required
for AfriRide’s proof surfaces to be considered valid, auditable, and
institution‑grade.

All items below must be satisfied **in full**.
There is no partial compliance.

---

## Governance & Lineage

✅ **Epoch lineage intact (Epoch 6 → Epoch 7)**  
- Parent–child epoch relationship preserved  
- No gaps, forks, or retroactive mutation  

✅ **ADRs present and consistent**  
- ADR‑0007‑afriride‑v0‑2 approved  
- ADR scope aligns with Epoch 7 declaration  
- No conflicting or superseding decisions  

---

## Artifact Integrity

✅ **AfriRide v0.1 artifacts frozen**  
- v0.1 code, claims, and evidence immutable  
- Baseline proof preserved as authoritative reference  

✅ **AfriRide v0.2 artifacts frozen**  
- v0.2 scenarios, execution handlers, and metrics immutable  
- Proof surface locked under Epoch 7  

✅ **Constitutional core untouched**  
- No modification to `core/constitutional/*`  
- All evolution layered externally  

---

## Determinism Enforcement

✅ **Determinism envelope enforced**  
- All execution paths operate within declared envelope  
- No randomness, heuristics, or implicit behavior  

✅ **Failure taxonomy enforced**  
- All failures explicitly declared  
- No undeclared or emergent failure paths  

---

## Replay Verification

✅ **Replay verifier passes**  
- Execution and replay hashes identical  
- Trace ordering preserved  
- State transitions replay identically  

✅ **Mandatory replay executed**  
- v0.1 replay validated  
- v0.2 multi‑scenario replay validated  

---

## Evidence & Claims Alignment

✅ **Executable evidence present**  
- Proof runnable via documented commands  
- No illustrative or non‑executable claims  

✅ **Claims match evidence**  
- All claims bounded to proven behavior  
- No performance, optimization, or market claims  
- Metrics (DDR, CC, DRR) align with observed output  

---

## Failure Conditions

✅ **No undeclared behavior paths**  
- No silent failure  
- No partial execution  
- No implicit fallback  

✅ **Deterministic refusal enforced**  
- Refusal explicit and trace‑bound  
- Refusal replays identically  

---

## Final Audit Assertion

If **all** items above are satisfied:

> ✅ **AfriRide is constitutionally valid, replay‑verifiable,
> and suitable for institutional audit and long‑term governance.**

If **any single item fails**:

> ❌ **The proof surface is invalidated in full.**

There is no partial correctness.
