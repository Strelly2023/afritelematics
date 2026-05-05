# AfriTech Epoch History — Schema Semantics

This directory contains the **authoritative, immutable epoch history**
for the AfriTech constitutional system.

Epoch files here are used for:
- constitutional replay verification
- temporal legitimacy auditing
- governance traceability
- external and regulatory review

This document explains **why multiple epoch schemas exist** and how
they MUST be interpreted.

---

## Epoch Schemas

AfriTech intentionally uses **two related but distinct epoch schemas**.

This distinction is **semantic**, not accidental.

### 1. `afritech.registry.history.v1`

**Used by:** Epochs 0–4  
**Purpose:** Canonical historical record of constitutional evolution

Characteristics:
- Represents **substantive constitutional epochs**
- Encodes changes that affect identity, authority, or enforcement
- Used for permanent, static historical storage
- Fully compatible with replay verification

Examples:
- Constitutional activation
- Registry schema evolution
- Attestation model changes

---

### 2. `afritech.registry.epoch.v1`

**Used by:** Epoch 5  
**Purpose:** Explicit normalization-era epoch representation

Characteristics:
- Represents a **CONSTITUTIONAL_NORMALIZATION_EPOCH**
- Advances time *without changing constitutional meaning*
- Exists to normalize, clarify, and make history replay-verifiable
- Does **not** change identity, authority, policy, or enforcement
- Explicitly classified as non-evolutionary

Epoch 5 documents:
- bookkeeping corrections
- explicit reseal metadata
- authority attribution normalization
- replay-legitimacy alignment

---

## Why Epoch 5 Uses a Different Schema

Epoch 5 was intentionally modeled using
`afritech.registry.epoch.v1` to make its role **unambiguous**.

This avoids conflating:
- **evolutionary epochs** (change meaning)
- **normalization epochs** (clarify meaning)

The schema difference acts as a **machine- and human-visible signal**
that Epoch 5:
- advances time,
- but does not advance constitutional power.

---

## Replay & Tooling Guarantees

Replay verification tools:
- accept both schemas
- treat both as fully authoritative
- enforce invariants consistently

Schema selection does **not** affect:
- replay validity
- sealing requirements
- epoch monotonicity
- authority legitimacy

---

## Mutation Policy

Epoch history files are **immutable once finalized**.

Normalization is achieved via:
- explicit normalization epochs (e.g. Epoch 5), or
- bookkeeping corrections recorded by ADRs

Silent rewriting is forbidden.

---

## Constitutional Principle

> **Schema differences must communicate intent, not hide it.**

Epoch schema divergence is therefore:
- intentional
- documented
- replay-safe
- constitutionally sound
