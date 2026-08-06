# NovaPay WP-001P Section 5B

## Customer, Account, and Wallet Integration Decision

- Implemented areas: 14
- Partial areas: 0
- Absent areas: 0
- Deferred areas: 0
- Not-required areas: 0
- Focused implementation required: NO
- Focused certification tests required: NO
- Section 5 decision: TEST_ONLY_CERTIFICATION_SUFFICIENT

## Receipt boundary

The Receipt aggregate remains module-local:

`afritech.novapay.domain.receipt.Receipt`

This classification does not authorize exporting Receipt through:

- `afritech.novapay.domain`
- `afritech.novapay`

## Governing rule

Only ABSENT contracts authorize production implementation.

PARTIAL contracts authorize narrowly scoped certification tests or
contract reconciliation.

IMPLEMENTED contracts must be preserved.

DEFERRED contracts require a later explicit work-package decision.

NOT_REQUIRED contracts must not introduce unnecessary runtime authority.

## Next action

Prepare Section 5C as preservation-focused certification tests for the implemented contracts.
