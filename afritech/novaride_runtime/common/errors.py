"""Runtime errors."""

from __future__ import annotations


class NovaRideRuntimeError(Exception):
    code = "NOVARIDE_RUNTIME_ERROR"


class InvalidTransition(NovaRideRuntimeError):
    code = "INVALID_TRANSITION"


class ConcurrencyConflict(NovaRideRuntimeError):
    code = "CONCURRENCY_CONFLICT"


class DuplicateCommand(NovaRideRuntimeError):
    code = "DUPLICATE_COMMAND"


class AuthorityDenied(NovaRideRuntimeError):
    code = "AUTHORITY_DENIED"


class BoundaryViolation(NovaRideRuntimeError):
    code = "BOUNDARY_VIOLATION"
