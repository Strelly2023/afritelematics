from __future__ import annotations


class OperationalVerificationError(RuntimeError):
    """Base error for operational verification failures."""


class InvalidTransitionError(OperationalVerificationError):
    """Raised when a capability state transition violates policy."""


class EvidencePolicyError(OperationalVerificationError):
    """Raised when evidence is expired, superseded, fabricated, or incomplete."""


class ApprovalPolicyError(OperationalVerificationError):
    """Raised when approval policy, role, or four-eyes rules fail."""
