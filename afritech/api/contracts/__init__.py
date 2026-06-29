"""Canonical API contracts for AfriRide pilot ingress."""

from afritech.api.contracts.rules import EventContractRules
from afritech.api.contracts.schema_registry_api import build_schema_registry_router, get_schema_registry
from afritech.api.contracts.schema_registry_middleware import SchemaRegistryMiddleware
from afritech.api.contracts.validator import EventContractValidator

__all__ = [
    "EventContractRules",
    "EventContractValidator",
    "SchemaRegistryMiddleware",
    "build_schema_registry_router",
    "get_schema_registry",
]
