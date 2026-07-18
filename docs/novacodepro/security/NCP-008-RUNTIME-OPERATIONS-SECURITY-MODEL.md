# NCP-008 Runtime Operations Security Model

Security properties implemented for NCP-008:

- deny by default
- authentication required
- tenant isolation enforced in repository lookups
- environment scoping on operational records
- approval-gated mutation for high-risk operations
- separation-of-duties checks for critical action approval
- action allowlisting rather than arbitrary shell execution
- output redaction through constrained telemetry adapters
- production mutation disabled by default
- evidence and audit generation on governed actions

Not claimed:

- live external provider access
- browser certification
- production mutation verification unless an approved live operation is executed
