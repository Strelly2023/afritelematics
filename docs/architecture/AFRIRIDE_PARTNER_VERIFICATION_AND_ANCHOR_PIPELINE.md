# AfriRide Partner Verification API And Anchor Publication Pipeline

Status: PARTNER VERIFICATION API AND ANCHOR PUBLICATION PIPELINE
Classification: REPLAY_LINKED_EXTERNAL_EVIDENCE_SURFACE

Purpose: define the bounded external verification surface for partners,
auditors, and institutional integrators.

This document is a design surface.
It is not a declaration that every external publisher, region, or partner flow
is already live at enterprise scale.

## Core Rule

```text
trace_hash + replay_hash + receipt_hash -> external anchor commitment
```

The partner verification surface exists to prove export integrity and replay
linkage. It does not transfer runtime authority to the partner channel.

The anchor proves export integrity. Replay remains the authority.

## Partner Verification API

Primary verification endpoint:

```text
POST /v1/partner/verify
GET /v1/partner/anchors/{anchor_id}
```

The API returns:

- `anchor_id`
- `publication_id`
- `verification_status`
- `commitment_hash`
- `publication_hash`
- `receipt_commitment`
- `evidence_pointer`

The API may:

- package replay-linked evidence for partner consumption
- reject mismatched partner expectations
- expose publication metadata

The API may not:

- mutate trace truth
- mutate replay truth
- declare a receipt valid without receipt evidence
- grant partner mutation authority

## SDK

The reference SDK surface is `PartnerVerificationClient`.

The SDK supports:

- request preparation
- local deterministic verification rehearsal
- response decoding and required-field validation

The SDK is a transport helper only.
It does not become an authority surface.

## Anchor Publication Pipeline

The anchor publication pipeline is:

```text
trace/replay/receipt evidence
-> external anchor commitment
-> publication envelope
-> publication target
-> external reference
-> partner verification packet
```

Required publication properties:

- deterministic commitment hash
- deterministic publication hash
- replay-linked tenant and region metadata
- publication target labeling
- receipt commitment for later lookup

## Multi-Region Publisher Lanes

Anchor publication must support multi-region publisher lanes without allowing
one region to rewrite another region's trace authority.

Required lane concepts:

- tenant-scoped publication
- region-scoped publication
- shared external network naming
- per-region external reference tracking

## Failure Discipline

Publication failure must remain evidence-complete.

Required outcomes:

- publication failure opens evidence-complete alert
- anchor packet remains inspectable even when unpublished
- verification rejection records mismatch reasons
- replay and trace investigation remain first-class

## Authority Boundary

This externalization surface permits only this bounded claim:

```text
partners can verify that exported evidence packets are trace-linked,
replay-linked, and publication-bound
```

It does not permit this claim:

```text
partners become the source of truth
external anchors replace replay
publication success proves operational correctness
```
