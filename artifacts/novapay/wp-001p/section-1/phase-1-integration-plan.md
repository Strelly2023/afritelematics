# NovaPay WP-001P — Phase 1 Integration and Certification Plan

## Certified baseline

WP-001A through WP-001O are complete.

Certified parent:

`9d6148433242c4e1734071bcca943d66d388a2c5`

## Canonical vocabulary

Canonical reconciliation aggregate:

- SettlementReconciliation

Non-canonical guessed name:

- ReconciliationRecord

Receipt aggregate:

- Canonical in `afritech.novapay.domain.receipt`
- Module-local integration anchor
- Not exported from `afritech.novapay.domain`
- Not exported from `afritech.novapay`

Receipt public-record anchors:

- ReceiptIntegrityEvidence
- ReceiptVerificationResult

Deferred:

- ReceiptPresentationSummary

## Planned slices

1. Section 1B — canonical Phase 1 domain matrix.
2. Section 2A — money, currency, exchange-rate and FX integration.
3. Section 2B — customer, wallet, account and balance integration.
4. Section 3A — transaction, ledger and journal integration.
5. Section 3B — transfer, remittance, settlement and reconciliation.
6. Section 4A — module-local Receipt reference integration.
7. Section 4B — Receipt evidence and verification integration.
8. Section 5A — lifecycle and authority-boundary compatibility.
9. Section 5B — serialization and deterministic replay.
10. Section 6A — package and top-level API certification.
11. Section 6B — import topology and runtime governance.
12. Section 7A — full Phase 1 regression and constitutional gates.
13. Section 8A — final evidence, staging and commit certification.

## Constraints

- Preserve the Receipt aggregate as module-local unless separately authorized.
- Use SettlementReconciliation as the canonical reconciliation aggregate.
- Do not add payment execution authority to domain records.
- Do not add ledger-posting authority to Receipt records.
- Do not add persistence or external-provider authority to immutable records.
- Preserve canonical class identity across authorized public surfaces.
- Preserve deterministic serialization and replay-safe imports.
- Preserve unrelated working-tree changes.
