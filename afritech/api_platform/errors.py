"""Shared API platform errors."""

from __future__ import annotations


class ApiPlatformError(RuntimeError):
    code = "API_PLATFORM_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class ApiRegistrationError(ApiPlatformError):
    code = "API_REGISTRATION_ERROR"


class ApiRouteConflict(ApiPlatformError):
    code = "API_ROUTE_CONFLICT"


class ApiCompatibilityError(ApiPlatformError):
    code = "API_COMPATIBILITY_ERROR"


class ApiAuthorizationError(ApiPlatformError):
    code = "API_AUTHORIZATION_ERROR"


class ApiValidationError(ApiPlatformError):
    code = "API_VALIDATION_ERROR"


class ApiIdempotencyError(ApiPlatformError):
    code = "API_IDEMPOTENCY_CONFLICT"


class ApiTenancyError(ApiPlatformError):
    code = "API_TENANCY_ERROR"

