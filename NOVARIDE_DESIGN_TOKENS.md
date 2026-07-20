# NovaRide Design Tokens

Repository: /Users/ostrinov/afritelematics
Branch: feature/novacodepro-unified-platform
Commit: 0ebce8bc57f568033f48035ac16a74562dff17e4
Timestamp: 2026-07-20T00:50:09.269547+00:00

The shared design foundation lives in `packages/novatech-design-system/src/index.ts`.

Tokens now cover:

- semantic color aliases for surface, text, border, action, success, warning, critical, information, disabled, and focus
- interaction states for default, pressed, focused, hovered, disabled, loading, success, warning, error, and selected
- component metadata for buttons, chips, empty states, safety actions, receipts, and evidence views
- role-specific navigation sets for rider, driver, operations, and support surfaces
- user-facing content guidance for emergency, failure, payment, and offline messaging

These tokens are reused by the rider and driver apps through their existing design-system adapters.
