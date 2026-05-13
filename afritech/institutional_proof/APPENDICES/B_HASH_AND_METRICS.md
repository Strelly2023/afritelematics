# Appendix B — Hashes and Metrics

This appendix records the **authoritative execution evidence**
supporting AfriRide’s Proof‑of‑Continuity claims.

All values listed here are **observed outputs** from executable runs,
not inferred or estimated results.  
They are replay‑verifiable and constitutionally binding.

---

## Recorded Decision Hashes

### AfriRide v0.1 — Baseline Proof (Epoch 6)

**Scenario:** Driver degradation (single failure scenario)

- Original execution hash:  
  `133bce54cac853941af8f567ddc853d0fda541f4814dc54d1f1424b594ce0e21`

- Replay execution hash:  
  `133bce54cac853941af8f567ddc853d0fda541f4814dc54d1f1424b594ce0e21`

✅ Hashes identical  
✅ Replay invariant satisfied

---

### AfriRide v0.2 — Multi‑Scenario Proof (Epoch 7)

Each scenario below was executed and replayed independently.

#### DRIVER_DROPOUT
- Execution hash:  
  `98b1f32210b641526c34a561f994d39001a763bd53e262f3a40ecd9c5be4c015`
- Replay hash:  
  `98b1f32210b641526c34a561f994d39001a763bd53e262f3a40ecd9c5be4c015`

✅ Hashes identical

---

#### DRIVER_REJECTION_CHAIN
- Execution hash:  
  `317e6307d1396e7d2e3464e172420d4336d0ef5ee8e11bdd97f39b39d9a9bae7`
- Replay hash:  
  `317e6307d1396e7d2e3464e172420d4336d0ef5ee8e11bdd97f39b39d9a9bae7`

✅ Hashes identical

---

#### TIMEOUT_EXCEEDED
- Execution hash:  
  `f2129baf771e8cae9a3950291fd997bb157e7931f45256f1838125d9f39e12d9`
- Replay hash:  
  `f2129baf771e8cae9a3950291fd997bb157e7931f45256f1838125d9f39e12d9`

✅ Hashes identical

---

## Metrics Summary

All metrics below are **measured**, not computed analytically.

### Decision Determinism Rate (DDR)

| Proof Surface | DDR |
|--------------|-----|
| AfriRide v0.1 | 1.0 |
| AfriRide v0.2 | 1.0 (all scenarios) |

DDR = 1.0 indicates perfect execution‑replay equivalence.

---

### Continuity Coverage (CC)

| Version | CC |
|-------|----|
| AfriRide v0.2 | 1.0 |

All declared failure scenarios preserved replay identity.

---

### Deterministic Refusal Rate (DRR)

| Version | DRR |
|-------|-----|
| AfriRide v0.2 | 1.0 |

All refusal outcomes were:
- explicit  
- deterministic  
- trace‑bound  
- replay‑identical  

---

## Replay Verifier Output

Replay verification was performed using the AfriTech replay verifier.

**Result:**
- ✅ Replay valid
- ✅ Constitutional lineage intact
- ✅ Determinism envelope respected
- ✅ No undeclared behavior detected

Replay verifier status: **VALID**

---

## Final Assertion

> **All recorded hashes and metrics satisfy the constitutional replay invariant.  
> No divergence was observed across any execution or replay.**

This appendix provides **numerical, reproducible evidence**
that AfriRide’s Proof‑of‑Continuity claims hold in full.
