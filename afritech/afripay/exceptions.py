"""AfriPay domain exceptions."""

from __future__ import annotations


class AfriPayError(ValueError):
    """Base error for deterministic AfriPay domain failures."""


class GuardViolation(AfriPayError):
    """Raised when an AfriPay governance or financial invariant fails."""


class DuplicateReference(AfriPayError):
    """Raised when an idempotent financial reference is reused incorrectly."""


class InsufficientFunds(AfriPayError):
    """Raised when an available wallet balance cannot cover a debit."""


class ProviderFailure(AfriPayError):
    """Raised when a selected payment rail cannot execute."""
