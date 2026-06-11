# AfriRide Partner Onboarding Kit

Status: PARTNER ONBOARDING KIT
Classification: LAUNCH_AND_ADOPTION_ENABLEMENT_SURFACE

Purpose: package the replay-backed partner verification system into an adoption
surface that enterprise partners can actually onboard against.

This kit is an enablement surface.
It is not a delegation of runtime authority.

## Onboarding Goal

Partners should be able to:

- understand the trust boundary
- install the SDK
- submit a bounded verification request
- rehearse verification locally
- map results to their own audit workflow

## Onboarding Sequence

```text
intro packet
-> API credentials and environment mapping
-> SDK installation
-> verification tutorial
-> sandbox anchor verification
-> production evidence review
```

## Partner Onboarding Kit Contents

- trust boundary summary
- API reference for `POST /v1/partner/verify`
- anchor lookup reference for `GET /v1/partner/anchors/{anchor_id}`
- sample request/response payloads
- replay-linked terminology glossary
- escalation and support path

## SDK Distribution

SDK distribution must remain deterministic and bounded.

Required distribution surfaces:

- versioned Python package surface
- pinned response schema expectations
- release note discipline for payload changes
- sandbox-first installation guidance

SDK distribution may improve transport ergonomics.
SDK distribution may not redefine verification truth.

## Verification Tutorials

Required tutorials:

- tutorial 1: local request preparation
- tutorial 2: first sandbox verification
- tutorial 3: mismatch diagnosis and rejection handling
- tutorial 4: audit handoff into partner compliance tooling

Every tutorial must preserve:

- trace-linked examples
- replay-linked examples
- explicit authority boundary language

## Support And Adoption Metrics

The onboarding kit should track:

- time to first verified anchor
- time to first rejected anchor diagnosis
- SDK version adoption
- partner sandbox completion rate

## Authority Boundary

This kit permits only this bounded claim:

```text
partners can onboard to a replay-backed verification protocol with documented
SDK and tutorial support
```

It does not permit this claim:

```text
partner onboarding grants mutation rights
SDK installation proves production trust
```
