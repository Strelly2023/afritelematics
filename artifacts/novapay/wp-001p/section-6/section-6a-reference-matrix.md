# NovaPay WP-001P Section 6A

## Receipt Cross-Domain Reference Matrix

| Domain | Receipt source status | Source evidence | Test evidence |
|---|---|---|---|
| transaction | EXPLICIT | transaction | transaction, transaction_id |
| transfer | EXPLICIT | transfer | transfer, transfer_id |
| remittance | EXPLICIT | remittance | remittance, remittance_id |
| settlement_batch | EXPLICIT | settlement, settlement_batch | settlement, settlement_batch, settlement_batch_id |
| settlement_reconciliation | EXPLICIT | reconciliation | reconciliation, reconciliation_id |
| customer | GENERIC_REFERENCE_COMPATIBLE | generic reference | customer, customer_id |
| wallet | EXPLICIT | wallet | wallet, wallet_id |
| financial_account | GENERIC_REFERENCE_COMPATIBLE | generic reference | financial_account, account_id, account |
| ledger_account | EXPLICIT | ledger | ledger, ledger_account |
| money_currency | EXPLICIT | money, amount, currency | money, amount, currency |
| balance_snapshot | GENERIC_REFERENCE_COMPATIBLE | generic reference | balance, snapshot |
