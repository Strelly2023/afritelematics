# Upgrade Process

1. Propose protocol change.
2. Add or update ADR.
3. Add invariant or test coverage.
4. Run hardening and adversarial suites.
5. Update docs.
6. Commit only after validation passes.

No upgrade may weaken replay, consensus, or state determinism.
