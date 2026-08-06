# NovaPay WP-001P Section 6B

## Receipt Cross-Domain Integration Decision

- Gap-matrix rows: 17
- Implemented areas: 16
- Partial areas: 1
- Absent areas: 0
- Deferred areas: 0
- Not-required areas: 0
- Focused implementation required: NO
- Focused certification tests required: YES
- Section 6 decision: FOCUSED_CERTIFICATION_TESTS_REQUIRED

## Receipt public boundary

The Receipt aggregate remains module-local:

`afritech.novapay.domain.receipt.Receipt`

This classification does not authorize exporting Receipt through:

- `afritech.novapay.domain`
- `afritech.novapay`

The following records remain canonical public exports:

- `ReceiptIntegrityEvidence`
- `ReceiptVerificationResult`

`ReceiptPresentationSummary` remains deferred.

## Generic reference contract

The canonical cross-domain reference mechanism remains:

- `ReceiptReference.reference_type`
- `ReceiptReference.reference_value`

A domain classified as `GENERIC_REFERENCE_COMPATIBLE` is supported by
this canonical reference pair without introducing direct aggregate imports.

## Governing rule

Only ABSENT contracts authorize production implementation.

PARTIAL contracts authorize narrowly scoped certification tests or
contract reconciliation.

IMPLEMENTED contracts must be preserved.

DEFERRED contracts require a later explicit work-package decision.

NOT_REQUIRED contracts must not introduce unnecessary runtime authority.

## Next action

Prepare Section 6C as focused certification tests for PARTIAL rows.
