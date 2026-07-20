# NovaRide Design System

Repository: /Users/ostrinov/afritelematics
Branch: feature/novacodepro-unified-platform
Commit: 0ebce8bc57f568033f48035ac16a74562dff17e4
Timestamp: 2026-07-20T10:58:00Z

The shared design foundation now covers:

- semantic color aliases for surface, text, border, action, success, warning, critical, information, disabled, and focus
- interaction states for default, pressed, focused, hovered, disabled, loading, success, warning, error, and selected
- component catalog metadata for buttons, chips, empty states, safety actions, receipts, and evidence views
- role-specific navigation groupings for rider, driver, operations, and support experiences
- content guidance for emergency, failure, payment, and offline messaging

Implementation source:

- [packages/novatech-design-system/src/index.ts](./packages/novatech-design-system/src/index.ts)

The rider and driver applications consume the shared design system through their existing adapter modules.
The operations portal now uses the same trust-first visual language through a separate local prototype surface.
