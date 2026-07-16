"""Protected configuration rules for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .errors import ProtectedConfigurationViolation


PROTECTED_SETTINGS = {
    "authentication_required": True,
    "authorization_required": True,
    "tenant_isolation_enabled": True,
    "audit_enabled": True,
    "evidence_enabled": True,
    "tls_required": True,
    "event_signature_required": True,
    "secret_provider": True,
    "database_encryption_enabled": True,
    "production_debug_enabled": False,
    "allow_memory_fallback": False,
    "allow_unsigned_events": False,
    "allow_cross_tenant_queries": False,
}


def validate_protected_configuration(values: Mapping[str, Any], *, environment: str) -> None:
    for key, expected in PROTECTED_SETTINGS.items():
        if key in values and values[key] != expected:
            raise ProtectedConfigurationViolation(f"protected_configuration_violation:{key}")
    if environment.lower() in {"production", "prod"} and values.get("allow_memory_fallback", False):
        raise ProtectedConfigurationViolation("production_memory_fallback_forbidden")


@dataclass(frozen=True, slots=True)
class ProtectedConfigurationView:
    values: Mapping[str, Any]

    def redacted(self) -> dict[str, Any]:
        return {key: ("***" if "secret" in key or "token" in key else value) for key, value in self.values.items()}


__all__ = ["PROTECTED_SETTINGS", "ProtectedConfigurationView", "validate_protected_configuration"]
