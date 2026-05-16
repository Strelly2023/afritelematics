"""
Shared invariant evaluation logic.

This module contains PURE invariant logic that must not depend on:
- runtime engine
- execution layer
- guards

It is the lowest-level reusable invariant abstraction.
"""


def evaluate_invariant(data):
    """
    Pure function.

    No side effects.
    No imports from runtime.engine.
    No imports from guards.

    Deterministic and replay-safe.
    """
    # Example placeholder logic
    if not data:
        return False

    return True