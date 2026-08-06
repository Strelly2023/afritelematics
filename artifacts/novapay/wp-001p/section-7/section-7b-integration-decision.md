# NovaPay WP-001P Section 7B

## Phase 1 End-to-End Integration Decision

- Gap-matrix rows: 18
- Implemented areas: 18
- Partial areas: 0
- Absent areas: 0
- Deferred areas: 0
- Not-required areas: 0
- Focused implementation required: NO
- Focused certification tests required: NO
- Section 7 decision: TEST_ONLY_CERTIFICATION_SUFFICIENT

## Canonical chain

Customer
→ Wallet / FinancialAccount
→ Transaction
→ LedgerAccount / JournalEntry
→ Transfer / Remittance
→ SettlementBatch
→ SettlementReconciliation
→ Receipt

## Receipt boundary

The Receipt aggregate remains module-local:

`afritech.novapay.domain.receipt.Receipt`

It is not exported through:

- `afritech.novapay.domain`
- `afritech.novapay`

The following Receipt records remain canonical public exports:

- `ReceiptIntegrityEvidence`
- `ReceiptVerificationResult`

`ReceiptPresentationSummary` remains deferred.

## Governing rule

Only ABSENT contracts authorize production implementation.

PARTIAL contracts authorize narrowly scoped certification tests or
compatibility reconciliation.

IMPLEMENTED contracts must be preserved.

DEFERRED contracts require a later explicit work-package decision.

NOT_REQUIRED contracts must not introduce unnecessary authority.

## Next action

Prepare Section 7C as preservation-focused end-to-end certification tests.
