# State Service API

`StateService` is a read-only facade over ledger-derived state.

## Methods

- `snapshot()`
- `refresh_from_ledger(ledger)`
- `load_state(state)`
- `get_ride(ride_id)`
- `get_receipt(receipt_id)`
- `get_account_balance(account_id)`
- `get_shipment(shipment_id)`
- `get_lot(lot_id)`
- `list_executions()`

## Properties

- Read-only
- Deterministic
- Ledger-derived
- Non-authoritative
