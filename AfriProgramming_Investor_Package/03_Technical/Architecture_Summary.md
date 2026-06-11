# Architecture Summary

## Layers

1. Design Layer: UML + SOLID.
2. Proposal Layer: immutable ToolingProposal artifacts.
3. Validation Layer: contracts, replay, rollback readiness.
4. Governance Layer: approval and rejection authority.
5. Activation Layer: controlled execution gate.
6. Runtime Layer: protected execution surface.
7. Verification Layer: autonomous verification agents, non-authoritative.
8. Distributed Layer: anomaly consensus and federation, pilot-level validation.

## Key Invariants

- Design is not authority.
- AI suggestions are not accepted code.
- Drift detection is not enforcement.
- Governance approval is required for activation.
- Runtime mutation remains denied outside controlled activation.
