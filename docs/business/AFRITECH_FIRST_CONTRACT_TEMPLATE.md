# AfriTech First Contract Template

Status: FIRST CONTRACT TEMPLATE
Classification: READY_TO_SEND_COMMERCIAL_TEMPLATE_SURFACE

Purpose: provide a first-pass contract template for the initial bounded AfriTech
engagement.

This template is a commercial drafting surface.
It is not legal advice and is not a signed contract.

## Contract Summary

- engagement type: bounded verification pilot
- workflow count: `1`
- duration: `45 days`
- pilot fee: `USD 18,000`

## Scope Clause

```text
AfriTech will provide a bounded verification pilot for one agreed workflow,
including replay-backed proof review, signed receipt access, bounded external
verification access, trust SLA reporting, and pilot review support.
```

## Runtime Surfaces Clause

```text
The pilot may include access to bounded runtime surfaces including:

- GET /ride/{ride_id}/replay
- GET /ride/{ride_id}/receipt
- POST /system/external-verify/{ride_id}
- GET /system/trust-sla
- WS /ws/system/trust
```

## Authority Boundary Clause

```text
Replay-backed evidence remains the authority for workflow verification.
Signed receipts remain portable proof artifacts.
External verification surfaces expose bounded verification outcomes.
Trust SLA surfaces explain operational thresholds and do not replace replay
authority.
```

## Commercial Clause

```text
The pilot fee covers one bounded workflow, one agreed success metric, one
review cadence, and the declared verification surfaces only. Additional
workflows, bespoke engineering, or expanded integration support require a
separate written agreement.
```

## Success Review Clause

```text
At pilot close, the parties will review the agreed workflow evidence, runtime
verification outcomes, trust SLA observations, and next-step expansion options.
```

## Non-Claim Clause

```text
This pilot agreement does not represent universal production certification,
unlimited system warranty, or unrestricted workflow coverage.
```

