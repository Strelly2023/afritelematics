# NovaScript Lifecycle

This is the first lifecycle diagram every NovaScript engineer, integrator, auditor, or adopting organization should understand.

```text
Prompt
  |
  v
Generation
  |
  v
Policy Evaluation
  |
  v
Governance Receipt
  |
  v
Certificate Chain
  |
  v
Assurance
  |
  v
Portable Package
  |
  v
Trust Exchange
  |
  v
Public Verification
```

## Lifecycle Stages

## Prompt

The initial engineering request. A prompt may ask NovaScript to generate, explain, debug, document, test, or analyze a software system.

## Generation

NovaScript routes the request through the model/provider layer and produces structured engineering artifacts.

## Policy Evaluation

The policy engine evaluates trust, risk, federation, and receipt requirements. Decisions are linked to policy versions and hashes.

## Governance Receipt

A deterministic receipt is issued for the governed decision. The receipt includes prompt/output hashes, trust score, status, sequence, and signature.

## Certificate Chain

NovaTrust CA issues a chain from root certificate to organization certificate to receipt certificate.

## Assurance

Continuous assurance evaluates trust drift, risk drift, policy drift, architecture drift, and compliance drift.

## Portable Package

The portable package bundles receipt, certificate, assurance, proof, explanation, and manifest hashes for offline verification.

## Trust Exchange

Federation records cross-organization trust exchange without exposing private internal data.

## Public Verification

Read-only public endpoints let external parties verify trust receipts, certificates, assurance reports, and portable packages.
