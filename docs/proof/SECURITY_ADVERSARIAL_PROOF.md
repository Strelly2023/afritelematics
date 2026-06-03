# Security / Adversarial Proof

## Document Classification

```text
STATUS: PRODUCTION PROOF GATE 6
CLASSIFICATION: ADVERSARIAL SECURITY EVIDENCE SURFACE
ROLE: PROVE HOSTILE INPUT CANNOT REDEFINE REPLAY TRUTH
BOUNDARY: HOSTILE INPUT MAY ATTACK INFRASTRUCTURE; HOSTILE INPUT MAY NOT REDEFINE TRUTH
```

This report documents Production Proof Gate 6.

The security / adversarial proof validates that hostile attempts against
infrastructure, providers, storage, workers, telemetry, timestamps, and mobile
clients are rejected before they can become truth authorities.

## Required Attack Rejections

```text
raw external input to core
fake replay hash
duplicate worker result
tampered event log
invalid partition id
timestamp manipulation
provider response injection
mobile replay spoofing
fake observability evidence
```

## Enforcement Surface

```text
afritech/security/adversarial_proof.py
afritech/tests/security/test_security_adversarial_proof.py
afritech/ci/security_adversarial_validator.py
docs/proof/SECURITY_ADVERSARIAL_PROOF.md
```

Hostile input may attack infrastructure.

Hostile input may not redefine truth, inject replay authority, spoof mobile
replay state, poison worker results, mutate storage evidence, invent partition
identity, alter replay-safe time, or promote observability into authority.

## Current Gate

```bash
python3 -m afritech.ci.security_adversarial_validator
```

Passing this gate means AfriTech preserves replay legitimacy under adversarial
pressure by rejecting hostile attempts to make infrastructure, providers,
storage, workers, telemetry, timestamps, or mobile clients become truth
authorities.
