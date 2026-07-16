"""Errors for the shared integration platform."""

from __future__ import annotations


class IntegrationError(RuntimeError):
    code = "INTEGRATION_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class IntegrationConfigurationError(IntegrationError):
    code = "INTEGRATION_CONFIGURATION_ERROR"


class IntegrationProviderError(IntegrationError):
    code = "INTEGRATION_PROVIDER_ERROR"


class IntegrationTimeoutError(IntegrationError):
    code = "INTEGRATION_TIMEOUT"


class IntegrationRateLimitError(IntegrationError):
    code = "INTEGRATION_RATE_LIMITED"


class IntegrationAuthenticationError(IntegrationError):
    code = "INTEGRATION_AUTHENTICATION_FAILED"


class IntegrationPermissionError(IntegrationError):
    code = "INTEGRATION_PERMISSION_DENIED"


class IntegrationCircuitOpenError(IntegrationError):
    code = "INTEGRATION_CIRCUIT_OPEN"


class IntegrationContractError(IntegrationError):
    code = "INTEGRATION_CONTRACT_MISMATCH"


class IntegrationSchemaError(IntegrationError):
    code = "INTEGRATION_SCHEMA_ERROR"

