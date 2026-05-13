# Limits and Non‑Claims

AfriRide is intentionally **limited by design**.

These limits are not gaps or omissions — they are **constitutional boundaries**
that preserve determinism, auditability, and long‑term correctness.
Anything outside these boundaries is explicitly **out of scope**.

---

## What AfriRide Does **Not** Claim

AfriRide makes **no claims** regarding:

- performance or throughput  
- efficiency or resource optimization  
- cost minimization or economic outcomes  
- user experience quality or usability  
- scalability or production readiness  
- market viability or commercial competitiveness  

AfriRide does not attempt to optimize outcomes, predict behavior,
or improve efficiency over time.

Including such claims would require nondeterminism, heuristics,
or empirical assumptions — all of which are constitutionally forbidden.

---

## Explicit Exclusions

AfriRide does **not** include:

- payments or financial logic  
- pricing, incentives, or marketplace dynamics  
- scoring, ranking, or optimization algorithms  
- machine learning or artificial intelligence  
- adaptive or self‑modifying behavior  
- real‑time clocks, delays, or asynchronous execution  
- external state dependencies (network, I/O, environment)  

These exclusions are deliberate and enforced.

---

## What AfriRide **Does** Claim

AfriRide makes **only** the following claims:

- **Correctness**  
  Decisions are correct with respect to declared rules and authority.

- **Determinism**  
  Identical inputs always produce identical outcomes.

- **Replay‑Verifiability**  
  Every execution can be replayed with identical traces and hashes.

- **Governed Evolution**  
  All change occurs through explicit ADRs and epoch transitions,
  without mutating historical artifacts.

These claims are **bounded, executable, and provable**.

---

## Why These Limits Matter

By refusing to claim performance, optimization, or market outcomes,
AfriRide avoids the most common sources of institutional failure:

- unverifiable promises  
- shifting definitions of success  
- hidden behavioral drift  
- erosion of auditability over time  

AfriRide demonstrates that **correctness must come before optimization**,
and governance must come before scale.

---

## Summary

AfriRide is not designed to be impressive.

It is designed to be **correct, explainable, and durable**.

> **AfriRide claims only what it can prove —
> and it proves only what it is willing to govern.**

These limits are what make the proof trustworthy.