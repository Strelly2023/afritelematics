"""Standard runtime errors for NovaTech executable product runtime."""

from __future__ import annotations


class RuntimeErrorBase(RuntimeError):
    code = "RUNTIME_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class ProductLoadRejected(RuntimeErrorBase):
    code = "RUNTIME_PRODUCT_NOT_ACTIVE"


class ProductContractViolation(RuntimeErrorBase):
    code = "RUNTIME_CONTRACT_INVALID"


class ProductRouteConflict(RuntimeErrorBase):
    code = "RUNTIME_ROUTE_CONFLICT"


class ProductHandlerConflict(RuntimeErrorBase):
    code = "RUNTIME_HANDLER_CONFLICT"


class ProductExecutionDenied(RuntimeErrorBase):
    code = "RUNTIME_PRODUCT_NOT_ACTIVE"


class ProductActivationBlocked(RuntimeErrorBase):
    code = "RUNTIME_ACTIVATION_BLOCKED"


class ProductVerificationFailed(RuntimeErrorBase):
    code = "RUNTIME_VERIFICATION_FAILED"


class ProductProvisioningFailed(RuntimeErrorBase):
    code = "RUNTIME_INFRASTRUCTURE_NOT_READY"


class ProductSecretAccessDenied(RuntimeErrorBase):
    code = "RUNTIME_SECRET_ACCESS_DENIED"


class ProtectedConfigurationViolation(RuntimeErrorBase):
    code = "RUNTIME_PROTECTED_CONFIGURATION_VIOLATION"


__all__ = [
    "ProductActivationBlocked",
    "ProductContractViolation",
    "ProductExecutionDenied",
    "ProductHandlerConflict",
    "ProductLoadRejected",
    "ProductProvisioningFailed",
    "ProductRouteConflict",
    "ProductSecretAccessDenied",
    "ProductVerificationFailed",
    "ProtectedConfigurationViolation",
    "RuntimeErrorBase",
]
