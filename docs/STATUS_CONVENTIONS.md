# Status Conventions

STATUS: PROVEN GOVERNANCE

All public-facing files must declare their status at the top.

## Allowed Statuses

`STATUS: PROVEN`

Verified through the executable system proof.

`STATUS: PROVEN ENTRY POINT`

Entry to the validated system.

`STATUS: FUTURE`

Not implemented, not validated, and not proof-admissible.

`STATUS: FUTURE GOVERNANCE`

Describes planned expansion, policy, or graduation rules.

`STATUS: PROVEN GOVERNANCE`

Defines rules that protect the proven system boundary.

## Rules

- A public-facing file without `STATUS:` is invalid.
- `PROVEN` files must not contain speculative claims.
- `FUTURE` files must not imply current capability.
- Only `PROVEN` surfaces may be referenced in system proof.
- Vision material must not appear in proof output, validators, CI results, or system logs.
