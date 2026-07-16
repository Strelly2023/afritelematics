"""Platform runtime configuration for governed backend modules."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class RuntimeLayer(StrEnum):
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    REGION = "region"
    PRODUCT = "product"
    TENANT = "tenant"
    FEATURE_FLAG = "feature_flag"
    EMERGENCY = "emergency"


class ConfigurationFieldType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True, slots=True)
class ProductConfigurationField:
    name: str
    type: ConfigurationFieldType | str
    default: Any = None
    required: bool = False
    description: str = ""
    minimum: int | float | None = None
    maximum: int | float | None = None
    enum: tuple[Any, ...] = ()
    secret: bool = False

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": str(self.type),
            "default": self.default,
            "required": self.required,
            "description": self.description,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "enum": list(self.enum),
            "secret": self.secret,
        }


@dataclass(frozen=True, slots=True)
class ProductConfigurationSchema:
    product_code: str
    schema_name: str
    schema_version: int
    fields: tuple[ProductConfigurationField, ...] = field(default_factory=tuple)
    description: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "description": self.description,
            "fields": [field.canonical_dict() for field in self.fields],
        }


@dataclass(frozen=True, slots=True)
class PlatformRuntimeSettings:
    environment: str
    region: str
    postgres_dsn: str = ""
    redis_dsn: str = ""
    event_broker_dsn: str = ""
    product_registry_path: str = ""
    configuration_registry_path: str = ""
    allow_memory_fallback: bool = True
    feature_flags: dict[str, bool] = field(default_factory=dict)
    platform_configuration: dict[str, Any] = field(default_factory=dict)
    environment_configuration: dict[str, Any] = field(default_factory=dict)
    region_configuration: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PlatformRuntimeSettings":
        values = env or os.environ
        return cls(
            environment=str(values.get("NOVATECH_RUNTIME_ENVIRONMENT") or values.get("AFRITECH_ENV") or "development"),
            region=str(values.get("NOVATECH_RUNTIME_REGION") or values.get("AFRITECH_REGION") or "AU"),
            postgres_dsn=str(values.get("NOVATECH_POSTGRES_DSN") or values.get("DATABASE_URL") or ""),
            redis_dsn=str(values.get("NOVATECH_REDIS_DSN") or values.get("REDIS_URL") or ""),
            event_broker_dsn=str(values.get("NOVATECH_EVENT_BROKER_DSN") or values.get("NATS_URL") or values.get("KAFKA_BOOTSTRAP_SERVERS") or ""),
            product_registry_path=str(values.get("NOVATECH_PRODUCT_REGISTRY_PATH") or ""),
            configuration_registry_path=str(values.get("NOVATECH_CONFIGURATION_REGISTRY_PATH") or ""),
            allow_memory_fallback=str(values.get("NOVATECH_ALLOW_MEMORY_FALLBACK", "true")).lower() == "true",
            feature_flags={
                "product_runtime_enabled": str(values.get("NOVATECH_PRODUCT_RUNTIME_ENABLED", "true")).lower() == "true",
                "registry_writes_enabled": str(values.get("NOVATECH_REGISTRY_WRITES_ENABLED", "true")).lower() == "true",
            },
        )

    def validate(self) -> None:
        environment = self.environment.strip().lower()
        if not self.region.strip():
            raise ValueError("platform_region_required")
        if environment in {"production", "prod"}:
            missing: list[str] = []
            if not self.postgres_dsn:
                missing.append("NOVATECH_POSTGRES_DSN")
            if not self.redis_dsn:
                missing.append("NOVATECH_REDIS_DSN")
            if not self.event_broker_dsn:
                missing.append("NOVATECH_EVENT_BROKER_DSN")
            if self.allow_memory_fallback:
                missing.append("NOVATECH_ALLOW_MEMORY_FALLBACK=false")
            if missing:
                raise ValueError("production_platform_settings_missing:" + ",".join(missing))


def create_platform_runtime_settings_from_env(env: Mapping[str, str] | None = None) -> PlatformRuntimeSettings:
    settings = PlatformRuntimeSettings.from_env(env)
    settings.validate()
    return settings


__all__ = [
    "ConfigurationFieldType",
    "PlatformRuntimeSettings",
    "ProductConfigurationField",
    "ProductConfigurationSchema",
    "RuntimeLayer",
    "create_platform_runtime_settings_from_env",
]
