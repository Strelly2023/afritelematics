# AfriTech Partner Live Demo Script (Runtime Boundary)

Status: AFRITECH PARTNER LIVE DEMO SCRIPT

Classification: BOUNDED PARTNER DEMO EXECUTION SURFACE

Purpose: provide a partner-ready live demo flow that shows the AfriTech runtime
truth model, the AfriRide application layer, and the FastAPI vs Django boundary
without overclaiming production maturity.

This script is a demo surface. It is not proof that every deployment is already
enterprise-certified.

## Demo Outcome

By the end of the demo, the partner should understand:

- AfriTech is the platform layer
- AfriRide is the application layer
- replay and receipts define admissible truth
- the dashboard observes, but does not define, truth
- the public verifier is bounded
- the FastAPI runtime and Django state layer are intentionally separated

## Demo Setup

Required:

- live deployment URL
- operator token path ready
- one trace / replay example
- one evidence / receipt example
- one public verification example
- dashboard reachable

Suggested warm-up checks:

```bash
curl http://<host>/health
curl http://<host>/public/verify/health
```

## Opening Script

Say:

> “This is a bounded production-style demo of the AfriTech runtime. The key
> claim is not that the UI is impressive. The key claim is that execution,
> replay, evidence, and verification line up.”

Then say:

> “AfriRide is the application surface. AfriTech is the verification and
> execution platform underneath it.”

## Demo Flow

### 1. Show runtime health

Show:

- `/health`
- dashboard landing page

Narration:

> “The service starts through a FastAPI runtime surface. This is the admission,
> orchestration, and verification layer.”

### 2. Show the runtime map

Narration:

> “Requests come into FastAPI, move through normalization and execution, then
> stateful domain work resolves through the Django-backed layer only where
> required.”

Use wording:

```text
FastAPI orchestrates.
Django stores state.
Replay proves.
Dashboard observes.
```

### 3. Show authenticated control surface

Demonstrate operator auth or token issuance.

Narration:

> “We distinguish public verification from authenticated control surfaces. Not
> every endpoint is public, and not every public endpoint is authoritative.”

### 4. Show replay / evidence / receipt alignment

Show:

- replay surface
- evidence summary
- receipt or proof response

Narration:

> “This is the core truth model. We are not asking you to trust a mutable
> dashboard row. We are asking you to inspect a replayable and receipt-bearing
> execution trail.”

### 5. Show public verification boundary

Show:

- `/public/verify/health`
- one bounded public verification endpoint

Narration:

> “External verification is available, but bounded. Public verification does not
> mutate system truth.”

### 6. Show operator dashboard

Narration:

> “The operator dashboard is intentionally an observation surface. It displays
> replay-backed health, guard state, and verification context. It does not
> become the source of truth itself.”

The dashboard is intentionally an observation surface.

### 7. Show architecture maturity point

Narration:

> “A major architectural lesson in this system is the separation between
> startup-safe orchestration code and Django-configured state code. That is why
> we formalized a runtime boundary contract.”

## Suggested Live Commands

```bash
curl http://<host>/health
curl http://<host>/public/verify/health
curl http://<host>/public/registry
```

If authenticated endpoints are available in the session:

```bash
curl -H "Authorization: Bearer <operator-token>" http://<host>/v1/system/status
curl -H "Authorization: Bearer <operator-token>" http://<host>/v1/traces
```

## Objection Handling

If asked “Is this just another dashboard?” say:

> “No. The dashboard is downstream of execution, replay, and receipt surfaces.”

If asked “Why mix FastAPI and Django?” say:

> “FastAPI gives us lean runtime orchestration and public/API flexibility.
> Django gives us mature stateful model infrastructure. The important thing is
> that the boundary is explicit.”

If asked “Can public users change truth?” say:

> “No. Public verification is read-only and bounded.”

## Non-Claims To Avoid

Do not say:

- all repo modules are production-active
- all mobile clients are part of the current live runtime
- the dashboard itself proves truth
- public verification replaces replay
- the deployment is already government-certified

## Closing Script

Say:

> “What we want you to take away is that AfriTech is not a UI-first trust claim.
> It is a runtime-first trust claim. AfriRide is one application running on that
> platform, and the evidence is designed to be replayed, checked, and verified.”
