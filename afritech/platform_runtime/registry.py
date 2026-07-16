"""Shared NovaTech backend product registry and runtime contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import inspect
import hashlib
import json
from pathlib import Path
from threading import RLock
from typing import Any, Protocol, TypeVar, runtime_checkable

import yaml

from .config import ConfigurationFieldType, PlatformRuntimeSettings, ProductConfigurationField, ProductConfigurationSchema, RuntimeLayer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKEND_REGISTRY_PATH = ROOT / "docs/registry/NOVATECH_BACKEND_REGISTRY.yaml"


class ProductRegistrationStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class ProductHealthStatus(StrEnum):
    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_json(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _safe_dict(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return str(value)
    if hasattr(value, "canonical_dict"):
        return value.canonical_dict()
    if isinstance(value, Mapping):
        return {str(key): _safe_dict(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe_dict(item) for item in value]
    if isinstance(value, list):
        return [_safe_dict(item) for item in value]
    return value


def _config_defaults(schema: ProductConfigurationSchema | None) -> dict[str, Any]:
    if schema is None:
        return {}
    defaults: dict[str, Any] = {}
    for field in schema.fields:
        if field.default is not None:
            defaults[field.name] = field.default
    return defaults


def _canonical_payload(registry: "ProductRuntimeRegistry") -> dict[str, Any]:
    return {
        "schema": "novatech.backend.registry.v1",
        "version": "1.0.0",
        "platform": registry.settings.environment,
        "region": registry.settings.region,
        "platform_configuration": dict(registry.platform_configuration),
        "environment_configuration": dict(registry.environment_configuration),
        "region_configuration": dict(registry.region_configuration),
        "feature_flags": dict(registry.feature_flags),
        "emergency_overrides": dict(registry.emergency_overrides),
        "tenant_configuration": {
            tenant_id: dict(values) for tenant_id, values in sorted(registry.tenant_configuration.items())
        },
        "products": [product.canonical_dict() for product in registry.products.values()],
        "command_catalogue": registry.list_commands(),
        "query_catalogue": registry.list_queries(),
    }


@dataclass(frozen=True, slots=True)
class RequestContext:
    tenant_id: str
    organization_id: str
    region: str
    actor_id: str
    request_id: str = ""
    correlation_id: str = ""
    environment: str = ""
    product_code: str = ""
    role: str = ""
    permissions: tuple[str, ...] = ()

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "region": self.region,
            "actor_id": self.actor_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "environment": self.environment,
            "product_code": self.product_code,
            "role": self.role,
            "permissions": list(self.permissions),
        }


@dataclass(frozen=True, slots=True)
class ProductConfigurationRevision:
    revision_id: str
    product_code: str
    layer: RuntimeLayer
    actor_id: str
    correlation_id: str
    tenant_id: str
    region: str
    values: dict[str, Any]
    reason: str
    created_at: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "product_code": self.product_code,
            "layer": str(self.layer),
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "tenant_id": self.tenant_id,
            "region": self.region,
            "values": dict(self.values),
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class BackendProductRegistration:
    product_code: str
    module_name: str
    version: str
    owner: str
    api_prefix: str
    health_path: str
    database_schema: str
    status: ProductRegistrationStatus = ProductRegistrationStatus.DRAFT
    configuration_schema: ProductConfigurationSchema | None = None
    required_services: tuple[str, ...] = ()
    registered_commands: tuple[str, ...] = ()
    registered_queries: tuple[str, ...] = ()
    registered_events: tuple[str, ...] = ()
    registered_consumers: tuple[str, ...] = ()
    registered_workers: tuple[str, ...] = ()
    infrastructure: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    health_status: ProductHealthStatus = ProductHealthStatus.UNKNOWN
    description: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    approval_reference: str = ""
    product_group: str = ""
    module_version: str = ""
    tags: tuple[str, ...] = ()
    configuration_history: tuple[ProductConfigurationRevision, ...] = ()

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "module_name": self.module_name,
            "version": self.version,
            "owner": self.owner,
            "api_prefix": self.api_prefix,
            "health_path": self.health_path,
            "database_schema": self.database_schema,
            "status": str(self.status),
            "configuration_schema": self.configuration_schema.canonical_dict() if self.configuration_schema else None,
            "required_services": list(self.required_services),
            "registered_commands": list(self.registered_commands),
            "registered_queries": list(self.registered_queries),
            "registered_events": list(self.registered_events),
            "registered_consumers": list(self.registered_consumers),
            "registered_workers": list(self.registered_workers),
            "infrastructure": dict(self.infrastructure),
            "configuration": dict(self.configuration),
            "health_status": str(self.health_status),
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approval_reference": self.approval_reference,
            "product_group": self.product_group,
            "module_version": self.module_version,
            "tags": list(self.tags),
            "configuration_history": [revision.canonical_dict() for revision in self.configuration_history],
        }


@runtime_checkable
class EventPublisher(Protocol):
    async def publish(self, event: Any, context: RequestContext) -> None: ...


@runtime_checkable
class AuditRecorder(Protocol):
    async def record(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        context: RequestContext,
        metadata: dict[str, Any],
    ) -> None: ...


@runtime_checkable
class PolicyEvaluator(Protocol):
    async def evaluate(
        self,
        policy_code: str,
        actor: dict[str, Any],
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]: ...


@runtime_checkable
class ProductConfigurationProvider(Protocol):
    async def get(self, product_code: str, key: str, tenant_id: str, region: str) -> object: ...


@runtime_checkable
class NovaTechProductBackend(Protocol):
    product_code: str
    version: str

    def register_commands(self, registry: "CommandRegistry") -> None: ...

    def register_queries(self, registry: "QueryRegistry") -> None: ...

    def register_routes(self, router: Any) -> None: ...

    def register_consumers(self, event_runtime: Any) -> None: ...

    def register_workers(self, worker_runtime: Any) -> None: ...

    def configuration_schema(self) -> dict[str, Any]: ...

    def health_checks(self) -> tuple[Any, ...]: ...

    def migrations(self) -> tuple[Any, ...]: ...


TCommand = TypeVar("TCommand")
TQuery = TypeVar("TQuery")


class CommandRegistry:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], tuple[str, Any]] = {}

    def register(self, product_code: str, command_type: type[Any], handler: Any) -> None:
        self._handlers[command_type] = (product_code, handler)

    async def dispatch(self, command: Any, context: RequestContext) -> Any:
        handler_entry = self._handlers.get(type(command))
        if handler_entry is None:
            raise KeyError(f"unknown command: {type(command).__name__}")
        product_code, handler = handler_entry
        if product_code != context.product_code and context.product_code:
            raise PermissionError("command_product_context_mismatch")
        result = handler.handle(command, context) if hasattr(handler, "handle") else handler(command, context)
        if inspect.isawaitable(result):
            return await result
        return result

    def list_commands(self) -> list[dict[str, Any]]:
        return [
            {"command_type": command_type.__name__, "product_code": product_code, "handler": handler.__class__.__name__}
            for command_type, (product_code, handler) in sorted(self._handlers.items(), key=lambda item: item[0].__name__)
        ]


class QueryRegistry:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], tuple[str, Any]] = {}

    def register(self, product_code: str, query_type: type[Any], handler: Any) -> None:
        self._handlers[query_type] = (product_code, handler)

    async def execute(self, query: Any, context: RequestContext) -> Any:
        handler_entry = self._handlers.get(type(query))
        if handler_entry is None:
            raise KeyError(f"unknown query: {type(query).__name__}")
        product_code, handler = handler_entry
        if product_code != context.product_code and context.product_code:
            raise PermissionError("query_product_context_mismatch")
        result = handler.handle(query, context) if hasattr(handler, "handle") else handler(query, context)
        if inspect.isawaitable(result):
            return await result
        return result

    def list_queries(self) -> list[dict[str, Any]]:
        return [
            {"query_type": query_type.__name__, "product_code": product_code, "handler": handler.__class__.__name__}
            for query_type, (product_code, handler) in sorted(self._handlers.items(), key=lambda item: item[0].__name__)
        ]


class ProductRuntimeRegistry:
    def __init__(
        self,
        *,
        path: Path = DEFAULT_BACKEND_REGISTRY_PATH,
        settings: PlatformRuntimeSettings | None = None,
        products: dict[str, BackendProductRegistration] | None = None,
        command_registry: CommandRegistry | None = None,
        query_registry: QueryRegistry | None = None,
        platform_configuration: dict[str, Any] | None = None,
        environment_configuration: dict[str, Any] | None = None,
        region_configuration: dict[str, Any] | None = None,
        tenant_configuration: dict[str, dict[str, Any]] | None = None,
        feature_flags: dict[str, bool] | None = None,
        emergency_overrides: dict[str, Any] | None = None,
        configuration_history: tuple[ProductConfigurationRevision, ...] = (),
    ) -> None:
        self.path = path
        self.settings = settings or PlatformRuntimeSettings.from_env()
        self.products = _seed_default_products() if products is None else products
        self.command_registry = command_registry or CommandRegistry()
        self.query_registry = query_registry or QueryRegistry()
        self.platform_configuration = platform_configuration or {}
        self.environment_configuration = environment_configuration or {}
        self.region_configuration = region_configuration or {}
        self.tenant_configuration = tenant_configuration or {}
        self.feature_flags = feature_flags or {}
        self.emergency_overrides = emergency_overrides or {}
        self.configuration_history = configuration_history
        self._lock = RLock()

    @classmethod
    def load(cls, path: Path = DEFAULT_BACKEND_REGISTRY_PATH) -> "ProductRuntimeRegistry":
        if not path.exists():
            return cls(path=path, products=_seed_default_products())
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, dict):
            raise RuntimeError("backend registry must be a mapping")
        settings = PlatformRuntimeSettings(
            environment=str(payload.get("platform", "development")),
            region=str(payload.get("region", "AU")),
            postgres_dsn="",
            redis_dsn="",
            event_broker_dsn="",
            product_registry_path=str(path),
            configuration_registry_path=str(path),
            allow_memory_fallback=True,
        )
        products = {
            item["product_code"]: _load_product(item)
            for item in payload.get("products", [])
        }
        history = tuple(
            ProductConfigurationRevision(
                revision_id=item["revision_id"],
                product_code=item["product_code"],
                layer=RuntimeLayer(item["layer"]),
                actor_id=item["actor_id"],
                correlation_id=item["correlation_id"],
                tenant_id=item["tenant_id"],
                region=item["region"],
                values=dict(item.get("values", {})),
                reason=item.get("reason", ""),
                created_at=item["created_at"],
            )
            for item in payload.get("configuration_history", [])
        )
        return cls(
            path=path,
            settings=settings,
            products=products,
            platform_configuration=dict(payload.get("platform_configuration", {})),
            environment_configuration=dict(payload.get("environment_configuration", {})),
            region_configuration=dict(payload.get("region_configuration", {})),
            tenant_configuration={key: dict(value) for key, value in payload.get("tenant_configuration", {}).items()},
            feature_flags={key: bool(value) for key, value in payload.get("feature_flags", {}).items()},
            emergency_overrides=dict(payload.get("emergency_overrides", {})),
            configuration_history=history,
        )

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = _canonical_payload(self)
            payload["manifest_hash"] = f"sha256:{_sha256_json(_normalize(payload))}"
            self.path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")

    def summary(self) -> dict[str, Any]:
        return {
            "schema": "novatech.backend.registry.v1",
            "path": str(self.path),
            "product_count": len(self.products),
            "command_count": len(self.command_registry.list_commands()),
            "query_count": len(self.query_registry.list_queries()),
            "configuration_history_count": len(self.configuration_history),
            "manifest_hash": self.manifest_hash(),
        }

    def manifest_hash(self) -> str:
        return f"sha256:{_sha256_json(_normalize(_canonical_payload(self)))}"

    def manifest(self) -> dict[str, Any]:
        return _canonical_payload(self)

    def list_products(self) -> tuple[dict[str, Any], ...]:
        return tuple(product.canonical_dict() for product in self.products.values())

    def get_product(self, product_code: str) -> dict[str, Any]:
        key = product_code.strip().lower()
        product = self.products.get(key)
        if product is None:
            raise KeyError(f"unknown product: {product_code}")
        return product.canonical_dict()

    def register_product(self, product: BackendProductRegistration) -> dict[str, Any]:
        with self._lock:
            key = product.product_code.strip().lower()
            self.products[key] = product
            self.save()
            return {"status": "registered", "product": product.canonical_dict(), "summary": self.summary()}

    def register_backend(self, backend: NovaTechProductBackend, *, owner: str, api_prefix: str, database_schema: str, health_path: str, required_services: tuple[str, ...] = (), infrastructure: dict[str, Any] | None = None) -> dict[str, Any]:
        schema = None
        if hasattr(backend, "configuration_schema"):
            schema_payload = backend.configuration_schema()
            if isinstance(schema_payload, Mapping):
                schema = _schema_from_dict(backend.product_code, schema_payload)
        product = BackendProductRegistration(
            product_code=backend.product_code,
            module_name=backend.__class__.__module__,
            version=str(backend.version),
            owner=owner,
            api_prefix=api_prefix,
            health_path=health_path,
            database_schema=database_schema,
            status=ProductRegistrationStatus.APPROVED,
            configuration_schema=schema,
            required_services=required_services,
            infrastructure=dict(infrastructure or {}),
            configuration=_config_defaults(schema),
            health_status=ProductHealthStatus.READY,
            module_version=str(backend.version),
        )
        return self.register_product(product)

    def register_configuration_schema(self, product_code: str, schema: ProductConfigurationSchema) -> dict[str, Any]:
        with self._lock:
            product = self._require_product(product_code)
            updated = BackendProductRegistration(
                product_code=product.product_code,
                module_name=product.module_name,
                version=product.version,
                owner=product.owner,
                api_prefix=product.api_prefix,
                health_path=product.health_path,
                database_schema=product.database_schema,
                status=product.status,
                configuration_schema=schema,
                required_services=product.required_services,
                registered_commands=product.registered_commands,
                registered_queries=product.registered_queries,
                registered_events=product.registered_events,
                registered_consumers=product.registered_consumers,
                registered_workers=product.registered_workers,
                infrastructure=dict(product.infrastructure),
                configuration=dict(product.configuration),
                health_status=product.health_status,
                description=product.description,
                created_at=product.created_at,
                updated_at=_now(),
                approval_reference=product.approval_reference,
                product_group=product.product_group,
                module_version=product.module_version,
                tags=product.tags,
                configuration_history=product.configuration_history,
            )
            self.products[product_code.lower()] = updated
            self.save()
            return {"status": "registered", "configuration_schema": schema.canonical_dict()}

    def list_commands(self) -> list[dict[str, Any]]:
        return self.command_registry.list_commands()

    def list_queries(self) -> list[dict[str, Any]]:
        return self.query_registry.list_queries()

    def resolve_configuration(self, product_code: str, tenant_id: str = "", region: str = "") -> dict[str, Any]:
        product = self._require_product(product_code)
        resolved: dict[str, Any] = {}
        resolved.update(self.platform_configuration)
        resolved.update(self.environment_configuration)
        resolved.update(self.region_configuration)
        resolved.update(product.configuration)
        if tenant_id and tenant_id in self.tenant_configuration:
            resolved.update(self.tenant_configuration[tenant_id])
        if region and region.upper() == self.settings.region.upper():
            resolved.update(self.feature_flags)
        resolved.update(self.emergency_overrides)
        return resolved

    def validate_configuration(self, product_code: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        product = self._require_product(product_code)
        schema = product.configuration_schema
        if schema is None:
            return {"valid": True, "product_code": product_code, "schema": None, "configuration": dict(payload)}
        errors: list[str] = []
        for field in schema.fields:
            if field.required and field.name not in payload:
                errors.append(f"missing:{field.name}")
                continue
            if field.name not in payload:
                continue
            value = payload[field.name]
            if field.type == ConfigurationFieldType.BOOLEAN and not isinstance(value, bool):
                errors.append(f"type:{field.name}:boolean")
            elif field.type == ConfigurationFieldType.INTEGER and not isinstance(value, int):
                errors.append(f"type:{field.name}:integer")
            elif field.type == ConfigurationFieldType.NUMBER and not isinstance(value, (int, float)):
                errors.append(f"type:{field.name}:number")
            elif field.type == ConfigurationFieldType.STRING and not isinstance(value, str):
                errors.append(f"type:{field.name}:string")
            elif field.type == ConfigurationFieldType.ARRAY and not isinstance(value, list):
                errors.append(f"type:{field.name}:array")
            elif field.type == ConfigurationFieldType.OBJECT and not isinstance(value, Mapping):
                errors.append(f"type:{field.name}:object")
            if field.enum and value not in field.enum:
                errors.append(f"enum:{field.name}")
            if isinstance(value, (int, float)) and field.minimum is not None and value < field.minimum:
                errors.append(f"minimum:{field.name}")
            if isinstance(value, (int, float)) and field.maximum is not None and value > field.maximum:
                errors.append(f"maximum:{field.name}")
        return {
            "valid": not errors,
            "product_code": product_code,
            "schema": schema.canonical_dict(),
            "errors": errors,
            "configuration": dict(payload),
        }

    def update_configuration(
        self,
        product_code: str,
        values: Mapping[str, Any],
        *,
        tenant_id: str = "",
        region: str = "",
        actor_id: str = "",
        correlation_id: str = "",
        reason: str = "",
        layer: RuntimeLayer = RuntimeLayer.PRODUCT,
    ) -> dict[str, Any]:
        validation = self.validate_configuration(product_code, values)
        if not validation["valid"]:
            return validation
        with self._lock:
            product = self._require_product(product_code)
            merged = {**product.configuration, **dict(values)}
            revision = ProductConfigurationRevision(
                revision_id=f"cfg-{hashlib.sha256(json.dumps(dict(values), sort_keys=True, default=str).encode('utf-8')).hexdigest()[:16]}",
                product_code=product_code,
                layer=layer,
                actor_id=actor_id,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                region=region,
                values=dict(values),
                reason=reason,
                created_at=_now(),
            )
            updated = BackendProductRegistration(
                product_code=product.product_code,
                module_name=product.module_name,
                version=product.version,
                owner=product.owner,
                api_prefix=product.api_prefix,
                health_path=product.health_path,
                database_schema=product.database_schema,
                status=product.status,
                configuration_schema=product.configuration_schema,
                required_services=product.required_services,
                registered_commands=product.registered_commands,
                registered_queries=product.registered_queries,
                registered_events=product.registered_events,
                registered_consumers=product.registered_consumers,
                registered_workers=product.registered_workers,
                infrastructure=dict(product.infrastructure),
                configuration=merged,
                health_status=product.health_status,
                description=product.description,
                created_at=product.created_at,
                updated_at=_now(),
                approval_reference=product.approval_reference,
                product_group=product.product_group,
                module_version=product.module_version,
                tags=product.tags,
                configuration_history=tuple(product.configuration_history) + (revision,),
            )
            self.products[product_code.lower()] = updated
            self.configuration_history = tuple(self.configuration_history) + (revision,)
            self.save()
            return {
                "valid": True,
                "product": updated.canonical_dict(),
                "revision": revision.canonical_dict(),
            }

    def set_platform_configuration(self, values: Mapping[str, Any]) -> None:
        self.platform_configuration = dict(values)
        self.save()

    def set_environment_configuration(self, values: Mapping[str, Any]) -> None:
        self.environment_configuration = dict(values)
        self.save()

    def set_region_configuration(self, values: Mapping[str, Any]) -> None:
        self.region_configuration = dict(values)
        self.save()

    def set_tenant_configuration(self, tenant_id: str, values: Mapping[str, Any]) -> None:
        self.tenant_configuration[tenant_id] = dict(values)
        self.save()

    def set_feature_flags(self, values: Mapping[str, bool]) -> None:
        self.feature_flags = {key: bool(value) for key, value in values.items()}
        self.save()

    def set_emergency_override(self, values: Mapping[str, Any]) -> None:
        self.emergency_overrides = dict(values)
        self.save()

    def list_configuration_history(self, product_code: str | None = None) -> tuple[dict[str, Any], ...]:
        if product_code:
            try:
                items = self._require_product(product_code).configuration_history
            except KeyError:
                items = ()
        else:
            items = self.configuration_history
        return tuple(item.canonical_dict() for item in items)

    def health_snapshot(self) -> dict[str, Any]:
        products = {}
        for product_code, product in self.products.items():
            products[product_code] = {
                "status": str(product.health_status if product.health_status else ProductHealthStatus.UNKNOWN),
                "database": "ready" if product.database_schema else "unknown",
                "cache": "ready" if product.required_services else "unknown",
                "event_consumers": "ready" if product.registered_consumers else "unknown",
                "workers": "ready" if product.registered_workers else "unknown",
                "websocket": "ready" if "websocket" in product.infrastructure else "unknown",
                "api_prefix": product.api_prefix,
                "health_path": product.health_path,
                "version": product.version,
                "owner": product.owner,
            }
        platform_status = "ready" if products else "degraded"
        return {
            "platform": "NovaTech",
            "status": platform_status,
            "products": products,
            "registry": self.summary(),
        }

    def _require_product(self, product_code: str) -> BackendProductRegistration:
        product = self.products.get(product_code.lower())
        if product is None:
            raise KeyError(f"unknown product: {product_code}")
        return product


def build_default_product_runtime_registry(path: Path | None = None) -> ProductRuntimeRegistry:
    target = path or DEFAULT_BACKEND_REGISTRY_PATH
    if target.exists():
        return ProductRuntimeRegistry.load(target)
    return ProductRuntimeRegistry(path=target, products=_seed_default_products())


def _schema_from_dict(product_code: str, payload: Mapping[str, Any]) -> ProductConfigurationSchema:
    fields = tuple(
        ProductConfigurationField(
            name=item["name"],
            type=ConfigurationFieldType(item["type"]),
            default=item.get("default"),
            required=bool(item.get("required", False)),
            description=item.get("description", ""),
            minimum=item.get("minimum"),
            maximum=item.get("maximum"),
            enum=tuple(item.get("enum", [])),
            secret=bool(item.get("secret", False)),
        )
        for item in payload.get("fields", [])
    )
    return ProductConfigurationSchema(
        product_code=product_code,
        schema_name=str(payload.get("schema_name") or f"{product_code}-config"),
        schema_version=int(payload.get("schema_version") or 1),
        fields=fields,
        description=str(payload.get("description") or ""),
    )


def _load_product(payload: Mapping[str, Any]) -> BackendProductRegistration:
    schema_payload = payload.get("configuration_schema")
    schema = _schema_from_dict(str(payload["product_code"]), schema_payload) if isinstance(schema_payload, Mapping) else None
    history = tuple(
        ProductConfigurationRevision(
            revision_id=item["revision_id"],
            product_code=item["product_code"],
            layer=RuntimeLayer(item["layer"]),
            actor_id=item["actor_id"],
            correlation_id=item["correlation_id"],
            tenant_id=item["tenant_id"],
            region=item["region"],
            values=dict(item.get("values", {})),
            reason=item.get("reason", ""),
            created_at=item["created_at"],
        )
        for item in payload.get("configuration_history", [])
    )
    return BackendProductRegistration(
        product_code=str(payload["product_code"]),
        module_name=str(payload["module_name"]),
        version=str(payload["version"]),
        owner=str(payload["owner"]),
        api_prefix=str(payload["api_prefix"]),
        health_path=str(payload["health_path"]),
        database_schema=str(payload["database_schema"]),
        status=ProductRegistrationStatus(payload.get("status", ProductRegistrationStatus.DRAFT)),
        configuration_schema=schema,
        required_services=tuple(payload.get("required_services", [])),
        registered_commands=tuple(payload.get("registered_commands", [])),
        registered_queries=tuple(payload.get("registered_queries", [])),
        registered_events=tuple(payload.get("registered_events", [])),
        registered_consumers=tuple(payload.get("registered_consumers", [])),
        registered_workers=tuple(payload.get("registered_workers", [])),
        infrastructure=dict(payload.get("infrastructure", {})),
        configuration=dict(payload.get("configuration", _config_defaults(schema))),
        health_status=ProductHealthStatus(payload.get("health_status", ProductHealthStatus.UNKNOWN)),
        description=str(payload.get("description", "")),
        created_at=str(payload.get("created_at", _now())),
        updated_at=str(payload.get("updated_at", _now())),
        approval_reference=str(payload.get("approval_reference", "")),
        product_group=str(payload.get("product_group", "")),
        module_version=str(payload.get("module_version", payload.get("version", ""))),
        tags=tuple(payload.get("tags", [])),
        configuration_history=history,
    )


def _default_schema(product_code: str, fields: list[dict[str, Any]], description: str) -> ProductConfigurationSchema:
    return ProductConfigurationSchema(
        product_code=product_code,
        schema_name=f"{product_code}-config",
        schema_version=1,
        fields=tuple(
            ProductConfigurationField(
                name=item["name"],
                type=ConfigurationFieldType(item["type"]),
                default=item.get("default"),
                required=bool(item.get("required", False)),
                description=item.get("description", ""),
                minimum=item.get("minimum"),
                maximum=item.get("maximum"),
                enum=tuple(item.get("enum", [])),
                secret=bool(item.get("secret", False)),
            )
            for item in fields
        ),
        description=description,
    )


def _seed_default_products() -> dict[str, BackendProductRegistration]:
    definitions = [
        {
            "product_code": "novaride",
            "module_name": "afritech.novaride_runtime.services",
            "version": "2026.07.0",
            "owner": "NovaRide Platform Team",
            "api_prefix": "/v1/novaride",
            "health_path": "/health/products/novaride",
            "database_schema": "novaride",
            "description": "Mobility and ride orchestration backend.",
            "required_services": ("identity", "policy", "audit", "evidence", "events", "redis", "postgres"),
            "registered_commands": ("RequestRide", "AcceptRide", "CompleteRide", "CancelRide"),
            "registered_queries": ("GetRide", "ListRides", "GetDriverAvailability"),
            "registered_events": ("ride.requested.v1", "ride.assigned.v1", "trip.completed.v1"),
            "registered_consumers": ("identity.verified.v1", "driver.location.updated.v1"),
            "registered_workers": ("dispatch-worker", "provider-health-worker", "outbox-worker"),
            "configuration_schema": _default_schema(
                "novaride",
                [
                    {"name": "dispatch_radius_km", "type": "integer", "default": 20, "minimum": 1, "maximum": 100},
                    {"name": "maximum_driver_candidates", "type": "integer", "default": 12, "minimum": 1, "maximum": 50},
                    {"name": "ride_request_timeout", "type": "integer", "default": 30, "minimum": 5, "maximum": 300},
                    {"name": "driver_location_ttl", "type": "integer", "default": 60, "minimum": 5, "maximum": 300},
                    {"name": "surge_pricing_enabled", "type": "boolean", "default": True},
                    {"name": "airport_rides_enabled", "type": "boolean", "default": False},
                ],
                "NovaRide product extension schema.",
            ),
            "configuration": {
                "dispatch_radius_km": 20,
                "maximum_driver_candidates": 12,
                "ride_request_timeout": 30,
                "driver_location_ttl": 60,
                "surge_pricing_enabled": True,
                "airport_rides_enabled": False,
            },
        },
        {
            "product_code": "novapay",
            "module_name": "afritech.core_platform.novapay_runtime",
            "version": "2026.07.0",
            "owner": "NovaPay Platform Team",
            "api_prefix": "/v1/novapay",
            "health_path": "/health/products/novapay",
            "database_schema": "novapay",
            "description": "Payments and settlement backend.",
            "required_services": ("identity", "policy", "audit", "evidence", "events", "redis", "postgres"),
            "registered_commands": ("InitiateTransfer", "CapturePayment", "RefundPayment", "ReconcileSettlement"),
            "registered_queries": ("GetWallet", "GetTransfer", "GetSettlement"),
            "registered_events": ("transfer.created.v1", "payment.captured.v1", "settlement.completed.v1"),
            "registered_consumers": ("identity.verified.v1", "policy.decision.v1"),
            "registered_workers": ("ledger-worker", "settlement-worker", "reconciliation-worker"),
            "configuration_schema": _default_schema(
                "novapay",
                [
                    {"name": "live_mode_enabled", "type": "boolean", "default": False},
                    {"name": "maximum_transfer_amount", "type": "number", "default": 1000.0, "minimum": 0},
                    {"name": "provider_timeout", "type": "integer", "default": 10, "minimum": 1, "maximum": 120},
                    {"name": "settlement_retry_limit", "type": "integer", "default": 3, "minimum": 0, "maximum": 10},
                    {"name": "manual_review_threshold", "type": "number", "default": 500.0, "minimum": 0},
                ],
                "NovaPay product extension schema.",
            ),
            "configuration": {
                "live_mode_enabled": False,
                "maximum_transfer_amount": 1000.0,
                "provider_timeout": 10,
                "settlement_retry_limit": 3,
                "manual_review_threshold": 500.0,
            },
        },
        {
            "product_code": "novacodepro",
            "module_name": "afritech.novacodepro.service_main",
            "version": "2026.07.0",
            "owner": "NovaCodePro Platform Team",
            "api_prefix": "/v1/solution-engineering",
            "health_path": "/health/products/novacodepro",
            "database_schema": "novacodepro",
            "description": "Enterprise solution engineering backend.",
            "required_services": ("identity", "policy", "audit", "evidence", "events", "postgres"),
            "registered_commands": ("CreateProject", "SubmitIdea", "ApproveRelease", "DeploySolution"),
            "registered_queries": ("GetProject", "ListProjects", "GetApprovals"),
            "registered_events": ("project.created.v1", "solution.blueprint.generated.v1", "release.approved.v1"),
            "registered_consumers": ("workflow.completed.v1", "approval.granted.v1"),
            "registered_workers": ("solution-worker", "approval-worker", "knowledge-worker"),
            "configuration_schema": _default_schema(
                "novacodepro",
                [
                    {"name": "ai_assistant_enabled", "type": "boolean", "default": True},
                    {"name": "workflow_fabric_enabled", "type": "boolean", "default": True},
                    {"name": "approval_gate_enforced", "type": "boolean", "default": True},
                    {"name": "generated_artifact_retention_days", "type": "integer", "default": 365, "minimum": 30, "maximum": 3650},
                ],
                "NovaCodePro product extension schema.",
            ),
            "configuration": {
                "ai_assistant_enabled": True,
                "workflow_fabric_enabled": True,
                "approval_gate_enforced": True,
                "generated_artifact_retention_days": 365,
            },
        },
        {
            "product_code": "novahealth",
            "module_name": "afritech.novahealth",
            "version": "2026.07.0",
            "owner": "NovaHealth Platform Team",
            "api_prefix": "/v1/novahealth",
            "health_path": "/health/products/novahealth",
            "database_schema": "novahealth",
            "description": "Healthcare workflows and regulated records backend.",
            "required_services": ("identity", "policy", "audit", "evidence", "events", "postgres"),
            "registered_commands": ("ScheduleAppointment", "UpdateClinicalRecord"),
            "registered_queries": ("GetPatient", "ListAppointments"),
            "registered_events": ("patient.registered.v1", "appointment.scheduled.v1"),
            "registered_workers": ("clinical-worker", "consent-worker"),
            "configuration_schema": _default_schema(
                "novahealth",
                [
                    {"name": "clinical_mode_enabled", "type": "boolean", "default": False},
                    {"name": "appointment_duration", "type": "integer", "default": 30, "minimum": 5, "maximum": 240},
                    {"name": "record_retention_years", "type": "integer", "default": 7, "minimum": 1, "maximum": 100},
                    {"name": "emergency_access_enabled", "type": "boolean", "default": False},
                ],
                "NovaHealth product extension schema.",
            ),
            "configuration": {
                "clinical_mode_enabled": False,
                "appointment_duration": 30,
                "record_retention_years": 7,
                "emergency_access_enabled": False,
            },
        },
        {
            "product_code": "novacommerce",
            "module_name": "afritech.novacommerce",
            "version": "2026.07.0",
            "owner": "NovaCommerce Platform Team",
            "api_prefix": "/v1/novacommerce",
            "health_path": "/health/products/novacommerce",
            "database_schema": "novacommerce",
            "description": "Commerce and merchant backend.",
            "required_services": ("identity", "policy", "audit", "evidence", "events", "postgres"),
            "registered_commands": ("ActivateMerchant", "CreateCatalogItem", "ProcessOrder"),
            "registered_queries": ("GetMerchant", "ListCatalogItems"),
            "registered_events": ("merchant.activated.v1", "order.processed.v1"),
            "registered_workers": ("catalog-worker", "order-worker"),
            "configuration_schema": _default_schema(
                "novacommerce",
                [
                    {"name": "catalog_sync_interval_seconds", "type": "integer", "default": 300, "minimum": 30, "maximum": 86400},
                    {"name": "checkout_timeout_seconds", "type": "integer", "default": 45, "minimum": 5, "maximum": 300},
                    {"name": "refunds_enabled", "type": "boolean", "default": True},
                ],
                "NovaCommerce product extension schema.",
            ),
            "configuration": {
                "catalog_sync_interval_seconds": 300,
                "checkout_timeout_seconds": 45,
                "refunds_enabled": True,
            },
        },
    ]
    return {
        item["product_code"]: BackendProductRegistration(
            product_code=item["product_code"],
            module_name=item["module_name"],
            version=item["version"],
            owner=item["owner"],
            api_prefix=item["api_prefix"],
            health_path=item["health_path"],
            database_schema=item["database_schema"],
            status=ProductRegistrationStatus.ACTIVE,
            configuration_schema=item["configuration_schema"],
            required_services=tuple(item["required_services"]),
            registered_commands=tuple(item["registered_commands"]),
            registered_queries=tuple(item["registered_queries"]),
            registered_events=tuple(item["registered_events"]),
            registered_consumers=tuple(item.get("registered_consumers", [])),
            registered_workers=tuple(item["registered_workers"]),
            infrastructure={
                "postgres_schema": item["database_schema"],
                "api_prefix": item["api_prefix"],
            },
            configuration=dict(item["configuration"]),
            health_status=ProductHealthStatus.READY,
            description=item["description"],
            product_group="shared-enterprise-platform",
            module_version=item["version"],
            tags=("platform", item["product_code"]),
        )
        for item in definitions
    }


__all__ = [
    "AuditRecorder",
    "BackendProductRegistration",
    "CommandRegistry",
    "DEFAULT_BACKEND_REGISTRY_PATH",
    "EventPublisher",
    "NovaTechProductBackend",
    "PolicyEvaluator",
    "ProductConfigurationProvider",
    "ProductConfigurationRevision",
    "ProductHealthStatus",
    "ProductRegistrationStatus",
    "ProductRuntimeRegistry",
    "QueryRegistry",
    "RequestContext",
    "build_default_product_runtime_registry",
]
