"""Metadata-driven enterprise data repository.

This layer persists product registrations, entity metadata, migrations,
relationships, lineage, contracts, and events as governed metadata rather than
as product-owned runtime tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import hashlib
import json
from typing import Any, Mapping

import yaml

from afritech.data_governance.enterprise import (
    ContractStatus,
    DataContract,
    DataDomainRegistryEntry,
    DataDomainStatus,
    DataEventDefinition,
    DataSharingLevel,
    EnterpriseDataGovernanceError,
    EnterpriseDataModel,
    ProductDataExtension,
    SchemaChangeClass,
    SharedEnterpriseEntity,
    default_enterprise_data_model,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA_PATH = ROOT / "docs/registry/NOVATECH_ENTERPRISE_METADATA.yaml"
METADATA_SCHEMA = "novatech.enterprise.metadata.v1"
METADATA_VERSION = "1.0.0"


class EnterpriseMetadataRepositoryError(RuntimeError):
    """Raised when enterprise metadata persistence fails."""


@dataclass(frozen=True, slots=True)
class EntityRelationship:
    source_entity: str
    target_entity: str
    relation_type: str
    cardinality: str = "many_to_one"
    description: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "relation_type": self.relation_type,
            "cardinality": self.cardinality,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class EntityMetadata:
    name: str
    schema_name: str
    owner: str
    source_of_truth: str
    classification: str
    product_code: str
    version: str = METADATA_VERSION
    status: str = "ACTIVE"
    description: str = ""
    business_meaning: str = ""
    privacy: str = ""
    llm_visibility: str = "approved_fields_only"
    confidence: str = "high"
    fields: tuple[str, ...] = field(default_factory=tuple)
    relationships: tuple[EntityRelationship, ...] = field(default_factory=tuple)
    indexes: tuple[str, ...] = field(default_factory=tuple)
    example_queries: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    ai_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("name", "schema_name", "owner", "source_of_truth", "classification", "product_code"):
            if not getattr(self, field_name).strip():
                raise EnterpriseDataGovernanceError(f"{field_name} is required")
        if not self.fields:
            raise EnterpriseDataGovernanceError("entity fields are required")
        if len(set(self.fields)) != len(self.fields):
            raise EnterpriseDataGovernanceError("entity fields must be unique")
        if len(set(self.indexes)) != len(self.indexes):
            raise EnterpriseDataGovernanceError("entity indexes must be unique")
        if len(set(self.example_queries)) != len(self.example_queries):
            raise EnterpriseDataGovernanceError("entity example_queries must be unique")
        if len(set(self.tags)) != len(self.tags):
            raise EnterpriseDataGovernanceError("entity tags must be unique")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "schema_name": self.schema_name,
            "owner": self.owner,
            "source_of_truth": self.source_of_truth,
            "classification": self.classification,
            "product_code": self.product_code,
            "version": self.version,
            "status": self.status,
            "description": self.description,
            "business_meaning": self.business_meaning,
            "privacy": self.privacy,
            "llm_visibility": self.llm_visibility,
            "confidence": self.confidence,
            "fields": list(self.fields),
            "relationships": [relationship.canonical_dict() for relationship in self.relationships],
            "indexes": list(self.indexes),
            "example_queries": list(self.example_queries),
            "tags": list(self.tags),
            "ai_metadata": dict(self.ai_metadata),
        }


@dataclass(frozen=True, slots=True)
class SchemaMigrationRecord:
    id: str
    product_code: str
    version: str
    checksum: str
    author: str
    approved_by: str
    applied_at: str
    rollback_version: str
    status: str = "APPROVED"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "product_code": self.product_code,
            "version": self.version,
            "checksum": self.checksum,
            "author": self.author,
            "approved_by": self.approved_by,
            "applied_at": self.applied_at,
            "rollback_version": self.rollback_version,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class DataLineageRecord:
    id: str
    source_product: str
    target_product: str
    data_type: str
    purpose: str
    path: tuple[str, ...]
    recorded_at: str
    evidence_hash: str
    classification: str = "CONFIDENTIAL"
    status: str = "ACTIVE"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_product": self.source_product,
            "target_product": self.target_product,
            "data_type": self.data_type,
            "purpose": self.purpose,
            "path": list(self.path),
            "recorded_at": self.recorded_at,
            "evidence_hash": self.evidence_hash,
            "classification": self.classification,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class DataProductPackage:
    product_code: str
    name: str
    owner: str
    schema_name: str
    version: str
    classification: str
    region: str
    description: str = ""
    entities: tuple[str, ...] = field(default_factory=tuple)
    contracts: tuple[str, ...] = field(default_factory=tuple)
    events: tuple[str, ...] = field(default_factory=tuple)
    migrations: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "name": self.name,
            "owner": self.owner,
            "schema_name": self.schema_name,
            "version": self.version,
            "classification": self.classification,
            "region": self.region,
            "description": self.description,
            "entities": list(self.entities),
            "contracts": list(self.contracts),
            "events": list(self.events),
            "migrations": list(self.migrations),
            "metadata": dict(self.metadata),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_json(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _canonical_content(model: EnterpriseDataModel, repository: "EnterpriseMetadataRepository") -> dict[str, Any]:
    return {
        "schema": METADATA_SCHEMA,
        "version": METADATA_VERSION,
        "shared_model": model.canonical_dict(),
        "products": [product.canonical_dict() for product in repository.products],
        "entities": [entity.canonical_dict() for entity in repository.entities],
        "relationships": [relationship.canonical_dict() for relationship in repository.relationships],
        "migrations": [migration.canonical_dict() for migration in repository.migrations],
        "lineage": [lineage.canonical_dict() for lineage in repository.lineage],
    }


class EnterpriseMetadataRepository:
    """Mutable but thread-safe metadata repository."""

    def __init__(
        self,
        path: Path = DEFAULT_METADATA_PATH,
        *,
        model: EnterpriseDataModel | None = None,
        products: tuple[DataProductPackage, ...] = (),
        entities: tuple[EntityMetadata, ...] = (),
        relationships: tuple[EntityRelationship, ...] = (),
        migrations: tuple[SchemaMigrationRecord, ...] = (),
        lineage: tuple[DataLineageRecord, ...] = (),
    ) -> None:
        self.path = path
        self.model = model or default_enterprise_data_model()
        self.products = products
        self.entities = entities
        self.relationships = relationships
        self.migrations = migrations
        self.lineage = lineage
        self._lock = RLock()

    @classmethod
    def load(cls, path: Path = DEFAULT_METADATA_PATH) -> "EnterpriseMetadataRepository":
        if not path.exists():
            return cls(path=path)
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, dict):
            raise EnterpriseMetadataRepositoryError("enterprise metadata file must be an object")
        shared_model = _load_shared_model(payload.get("shared_model"))
        return cls(
            path=path,
            model=shared_model,
            products=tuple(_load_product(item) for item in payload.get("products", []) or []),
            entities=tuple(_load_entity(item) for item in payload.get("entities", []) or []),
            relationships=tuple(_load_relationship(item) for item in payload.get("relationships", []) or []),
            migrations=tuple(_load_migration(item) for item in payload.get("migrations", []) or []),
            lineage=tuple(_load_lineage(item) for item in payload.get("lineage", []) or []),
        )

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = _canonical_content(self.model, self)
            payload["manifest_hash"] = _sha256_json(_normalize(payload))
            self.path.write_text(
                yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
                encoding="utf-8",
            )

    def summary(self) -> dict[str, Any]:
        return {
            "schema": METADATA_SCHEMA,
            "version": METADATA_VERSION,
            "path": str(self.path),
            "product_count": len(self.products),
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "migration_count": len(self.migrations),
            "lineage_count": len(self.lineage),
            "shared_entity_count": len(self.model.shared_entities),
            "contract_count": len(self.model.contracts),
            "event_count": len(self.model.events),
            "manifest_hash": self.manifest_hash(),
        }

    def manifest_hash(self) -> str:
        return f"sha256:{_sha256_json(_normalize(_canonical_content(self.model, self)))}"

    def list_products(self) -> tuple[dict[str, Any], ...]:
        return tuple(product.canonical_dict() for product in self.products)

    def get_product(self, product_code: str) -> dict[str, Any]:
        normalized = product_code.strip().lower()
        for product in self.products:
            if product.product_code.lower() == normalized:
                return product.canonical_dict()
        raise EnterpriseMetadataRepositoryError(f"unknown product: {product_code}")

    def list_entities(self) -> tuple[dict[str, Any], ...]:
        return tuple(entity.canonical_dict() for entity in self.entities) + tuple(
            entity.canonical_dict()
            for entity in self._shared_entities_as_metadata()
        )

    def get_entity(self, name: str) -> dict[str, Any]:
        normalized = name.strip().lower()
        for entity in self.entities:
            if entity.name.lower() == normalized:
                return entity.canonical_dict()
        for entity in self._shared_entities_as_metadata():
            if entity.name.lower() == normalized:
                return entity.canonical_dict()
        raise EnterpriseMetadataRepositoryError(f"unknown entity: {name}")

    def list_relationships(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.canonical_dict() for item in self.relationships)

    def list_migrations(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.canonical_dict() for item in self.migrations)

    def get_migration(self, migration_id: str) -> dict[str, Any]:
        normalized = migration_id.strip().lower()
        for migration in self.migrations:
            if migration.id.lower() == normalized:
                return migration.canonical_dict()
        raise EnterpriseMetadataRepositoryError(f"unknown migration: {migration_id}")

    def list_lineage(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.canonical_dict() for item in self.lineage)

    def get_lineage(self, lineage_id: str) -> dict[str, Any]:
        normalized = lineage_id.strip().lower()
        for lineage in self.lineage:
            if lineage.id.lower() == normalized:
                return lineage.canonical_dict()
        raise EnterpriseMetadataRepositoryError(f"unknown lineage record: {lineage_id}")

    def list_contracts(self) -> tuple[dict[str, Any], ...]:
        return tuple(contract.canonical_dict() for contract in self.model.contracts)

    def list_events(self) -> tuple[dict[str, Any], ...]:
        return tuple(event.canonical_dict() for event in self.model.events)

    def get_dashboard(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "products": self.list_products(),
            "entities": self.list_entities(),
            "relationships": self.list_relationships(),
            "contracts": self.list_contracts(),
            "events": self.list_events(),
            "migrations": self.list_migrations(),
            "lineage": self.list_lineage(),
        }

    def search(self, query: str) -> dict[str, Any]:
        normalized = query.strip().lower()
        if not normalized:
            return {"query": query, "results": []}
        results: list[dict[str, Any]] = []
        for entity in self.list_entities():
            haystack = " ".join(
                str(entity.get(key, ""))
                for key in ("name", "schema_name", "owner", "source_of_truth", "description", "business_meaning")
            ).lower()
            if normalized in haystack:
                results.append({"type": "entity", "item": entity})
        for product in self.list_products():
            haystack = " ".join(str(product.get(key, "")) for key in ("product_code", "name", "owner", "schema_name")).lower()
            if normalized in haystack:
                results.append({"type": "product", "item": product})
        for contract in self.list_contracts():
            haystack = " ".join(str(contract.get(key, "")) for key in ("contract_id", "producer_product", "consumer_product", "data_type", "purpose")).lower()
            if normalized in haystack:
                results.append({"type": "contract", "item": contract})
        for event in self.list_events():
            haystack = " ".join(str(event.get(key, "")) for key in ("event_type", "producer_product", "topic")).lower()
            if normalized in haystack:
                results.append({"type": "event", "item": event})
        return {"query": query, "results": results}

    def register_product(
        self,
        *,
        product_code: str,
        name: str,
        owner: str,
        schema_name: str,
        version: str,
        classification: str,
        region: str,
        description: str = "",
        metadata: Mapping[str, Any] | None = None,
        entities: tuple[EntityMetadata, ...] = (),
        extensions: tuple[ProductDataExtension, ...] = (),
        contracts: tuple[DataContract, ...] = (),
        events: tuple[DataEventDefinition, ...] = (),
        migrations: tuple[SchemaMigrationRecord, ...] = (),
    ) -> dict[str, Any]:
        with self._lock:
            product = DataProductPackage(
                product_code=product_code,
                name=name,
                owner=owner,
                schema_name=schema_name,
                version=version,
                classification=classification,
                region=region,
                description=description,
                entities=tuple(entity.name for entity in entities),
                contracts=tuple(contract.contract_id for contract in contracts),
                events=tuple(event.event_type for event in events),
                migrations=tuple(migration.id for migration in migrations),
                metadata=dict(metadata or {}),
            )
            self.products = _upsert_product(self.products, product)
            self.entities = _upsert_many(self.entities, entities, key=lambda item: item.name)
            self.relationships = self.relationships
            self.migrations = _upsert_many(self.migrations, migrations, key=lambda item: item.id)
            self.model = self.model.register_product_domain(
                DataDomainRegistryEntry(
                    id=f"{product_code.lower()}_domain",
                    product_code=product_code,
                    name=name,
                    owner=owner,
                    schema_name=schema_name,
                    version=version,
                    status=DataDomainStatus.ACTIVE,
                    classification=classification,
                    region=region,
                    created_at=_now(),
                ),
                extensions=extensions,
                contracts=contracts,
                events=events,
            )
            self.save()
            return {"status": "registered", "product": product.canonical_dict(), "summary": self.summary()}

    def register_entity(self, entity: EntityMetadata) -> dict[str, Any]:
        with self._lock:
            self.entities = _upsert_entity(self.entities, entity)
            self.save()
            return {"status": "registered", "entity": entity.canonical_dict()}

    def register_relationship(self, relationship: EntityRelationship) -> dict[str, Any]:
        with self._lock:
            self.relationships = _upsert_relationship(self.relationships, relationship)
            self.save()
            return {"status": "registered", "relationship": relationship.canonical_dict()}

    def register_migration(self, migration: SchemaMigrationRecord) -> dict[str, Any]:
        with self._lock:
            self.migrations = _upsert_migration(self.migrations, migration)
            self.save()
            return {"status": "registered", "migration": migration.canonical_dict()}

    def record_lineage(self, lineage: DataLineageRecord) -> dict[str, Any]:
        with self._lock:
            self.lineage = _upsert_lineage(self.lineage, lineage)
            self.save()
            return {"status": "recorded", "lineage": lineage.canonical_dict()}

    def register_contract(self, contract: DataContract) -> dict[str, Any]:
        with self._lock:
            self.model = self.model.with_contract(contract)
            self.save()
            return {"status": "registered", "contract": contract.canonical_dict()}

    def register_event(self, event: DataEventDefinition) -> dict[str, Any]:
        with self._lock:
            self.model = self.model.with_event(event)
            self.save()
            return {"status": "registered", "event": event.canonical_dict()}

    def product_entities(self, product_code: str) -> tuple[dict[str, Any], ...]:
        normalized = product_code.strip().lower()
        entities = [entity.canonical_dict() for entity in self.entities if entity.product_code.lower() == normalized]
        entities.extend(
            entity.canonical_dict()
            for entity in self._shared_entities_as_metadata()
            if entity.product_code.lower() == normalized or entity.source_of_truth.lower() == normalized
        )
        return tuple(entities)

    def ai_metadata(self) -> dict[str, Any]:
        return {
            "entities": [
                {
                    "name": entity.name,
                    "business_meaning": entity.business_meaning or entity.description,
                    "owner": entity.owner,
                    "privacy": entity.privacy,
                    "llm_visibility": entity.llm_visibility,
                    "example_queries": list(entity.example_queries),
                    "confidence": entity.confidence,
                }
                for entity in self.list_entity_objects()
            ]
        }

    def list_entity_objects(self) -> tuple[EntityMetadata, ...]:
        return self.entities + tuple(self._shared_entities_as_metadata())

    def _shared_entities_as_metadata(self) -> tuple[EntityMetadata, ...]:
        model = self.model
        return tuple(
            EntityMetadata(
                name=entity.name,
                schema_name=_shared_entity_schema(entity),
                owner=entity.source_of_truth,
                source_of_truth=entity.source_of_truth,
                classification=entity.classification,
                product_code=entity.source_of_truth,
                description=entity.description,
                business_meaning=entity.description or entity.name,
                privacy=entity.classification,
                llm_visibility="approved_fields_only",
                confidence="high",
                fields=entity.fields,
                ai_metadata={"shared": True, "sharing_level": entity.sharing_level.value},
            )
            for entity in model.shared_entities
        )


def build_default_metadata_repository(path: Path | None = None) -> EnterpriseMetadataRepository:
    return EnterpriseMetadataRepository.load(path or DEFAULT_METADATA_PATH)


def _load_shared_model(payload: Any) -> EnterpriseDataModel:
    if not isinstance(payload, Mapping):
        return default_enterprise_data_model()
    shared_entities = tuple(
        SharedEnterpriseEntity(
            name=item["name"],
            source_of_truth=item["source_of_truth"],
            fields=tuple(item["fields"]),
            classification=item["classification"],
            sharing_level=DataSharingLevel(item.get("sharing_level", DataSharingLevel.ENTERPRISE.value)),
            description=item.get("description", ""),
        )
        for item in payload.get("shared_entities", [])
    )
    product_domains = tuple(
        DataDomainRegistryEntry(
            id=item["id"],
            product_code=item["product_code"],
            name=item["name"],
            owner=item["owner"],
            schema_name=item["schema_name"],
            version=item["version"],
            status=DataDomainStatus(item["status"]),
            classification=item["classification"],
            region=item["region"],
            created_at=item["created_at"],
        )
        for item in payload.get("product_domains", [])
    )
    product_extensions = tuple(
        ProductDataExtension(
            product_code=item["product_code"],
            base_entity=item["base_entity"],
            table_name=item["table_name"],
            fields=tuple(item["fields"]),
            owner=item["owner"],
            classification=item.get("classification", "INTERNAL"),
        )
        for item in payload.get("product_extensions", [])
    )
    contracts = tuple(
        DataContract(
            contract_id=item["contract_id"],
            producer_product=item["producer_product"],
            consumer_product=item["consumer_product"],
            data_type=item["data_type"],
            schema_version=int(item["schema_version"]),
            purpose=item["purpose"],
            allowed_fields=tuple(item["allowed_fields"]),
            retention_policy=item["retention_policy"],
            consent_required=bool(item["consent_required"]),
            status=ContractStatus(item["status"]),
            sharing_level=DataSharingLevel(item.get("sharing_level", DataSharingLevel.ENTERPRISE.value)),
            schema_change=SchemaChangeClass(item.get("schema_change", SchemaChangeClass.COMPATIBLE.value)),
            classification=item["classification"],
            topic=item.get("topic", ""),
        )
        for item in payload.get("contracts", [])
    )
    events = tuple(
        DataEventDefinition(
            event_type=item["event_type"],
            event_version=int(item["event_version"]),
            producer_product=item["producer_product"],
            topic=item["topic"],
            payload_fields=tuple(item["payload_fields"]),
            consumers=tuple(item["consumers"]),
            classification=item["classification"],
            sharing_level=DataSharingLevel(item.get("sharing_level", DataSharingLevel.ENTERPRISE.value)),
            schema_change=SchemaChangeClass(item.get("schema_change", SchemaChangeClass.COMPATIBLE.value)),
            retention_policy=item.get("retention_policy", "AUDIT"),
        )
        for item in payload.get("events", [])
    )
    return EnterpriseDataModel(
        shared_entities=shared_entities or default_enterprise_data_model().shared_entities,
        product_domains=product_domains or default_enterprise_data_model().product_domains,
        product_extensions=product_extensions or default_enterprise_data_model().product_extensions,
        contracts=contracts or default_enterprise_data_model().contracts,
        events=events or default_enterprise_data_model().events,
        version=str(payload.get("version") or METADATA_VERSION),
        generated_at=str(payload.get("generated_at") or _now()),
    )


def _load_product(payload: Any) -> DataProductPackage:
    if not isinstance(payload, Mapping):
        raise EnterpriseMetadataRepositoryError("product entry must be an object")
    return DataProductPackage(
        product_code=payload["product_code"],
        name=payload["name"],
        owner=payload["owner"],
        schema_name=payload["schema_name"],
        version=payload["version"],
        classification=payload["classification"],
        region=payload["region"],
        description=payload.get("description", ""),
        entities=tuple(payload.get("entities", [])),
        contracts=tuple(payload.get("contracts", [])),
        events=tuple(payload.get("events", [])),
        migrations=tuple(payload.get("migrations", [])),
        metadata=dict(payload.get("metadata", {})),
    )


def _load_entity(payload: Any) -> EntityMetadata:
    if not isinstance(payload, Mapping):
        raise EnterpriseMetadataRepositoryError("entity entry must be an object")
    return EntityMetadata(
        name=payload["name"],
        schema_name=payload["schema_name"],
        owner=payload["owner"],
        source_of_truth=payload["source_of_truth"],
        classification=payload["classification"],
        product_code=payload["product_code"],
        version=payload.get("version", METADATA_VERSION),
        status=payload.get("status", "ACTIVE"),
        description=payload.get("description", ""),
        business_meaning=payload.get("business_meaning", ""),
        privacy=payload.get("privacy", ""),
        llm_visibility=payload.get("llm_visibility", "approved_fields_only"),
        confidence=payload.get("confidence", "high"),
        fields=tuple(payload.get("fields", [])),
        relationships=tuple(_load_relationship(item) for item in payload.get("relationships", [])),
        indexes=tuple(payload.get("indexes", [])),
        example_queries=tuple(payload.get("example_queries", [])),
        tags=tuple(payload.get("tags", [])),
        ai_metadata=dict(payload.get("ai_metadata", {})),
    )


def _load_relationship(payload: Any) -> EntityRelationship:
    if not isinstance(payload, Mapping):
        raise EnterpriseMetadataRepositoryError("relationship entry must be an object")
    return EntityRelationship(
        source_entity=payload["source_entity"],
        target_entity=payload["target_entity"],
        relation_type=payload["relation_type"],
        cardinality=payload.get("cardinality", "many_to_one"),
        description=payload.get("description", ""),
    )


def _load_migration(payload: Any) -> SchemaMigrationRecord:
    if not isinstance(payload, Mapping):
        raise EnterpriseMetadataRepositoryError("migration entry must be an object")
    return SchemaMigrationRecord(
        id=payload["id"],
        product_code=payload["product_code"],
        version=payload["version"],
        checksum=payload["checksum"],
        author=payload["author"],
        approved_by=payload["approved_by"],
        applied_at=payload["applied_at"],
        rollback_version=payload["rollback_version"],
        status=payload.get("status", "APPROVED"),
    )


def _load_lineage(payload: Any) -> DataLineageRecord:
    if not isinstance(payload, Mapping):
        raise EnterpriseMetadataRepositoryError("lineage entry must be an object")
    return DataLineageRecord(
        id=payload["id"],
        source_product=payload["source_product"],
        target_product=payload["target_product"],
        data_type=payload["data_type"],
        purpose=payload["purpose"],
        path=tuple(payload.get("path", [])),
        recorded_at=payload["recorded_at"],
        evidence_hash=payload["evidence_hash"],
        classification=payload.get("classification", "CONFIDENTIAL"),
        status=payload.get("status", "ACTIVE"),
    )


def _shared_entity_schema(entity: SharedEnterpriseEntity) -> str:
    if entity.name in {"Country", "Currency", "Language"}:
        return "reference"
    if entity.name in {"AuditEvent", "Evidence"}:
        return "audit"
    if entity.name in {"Consent"}:
        return "consent"
    if entity.name in {"Policy", "Role", "Permission"}:
        return "governance"
    return "core"


def _upsert_product(items: tuple[DataProductPackage, ...], item: DataProductPackage) -> tuple[DataProductPackage, ...]:
    remaining = [existing for existing in items if existing.product_code.lower() != item.product_code.lower()]
    remaining.append(item)
    return tuple(remaining)


def _upsert_entity(items: tuple[EntityMetadata, ...], item: EntityMetadata) -> tuple[EntityMetadata, ...]:
    remaining = [existing for existing in items if existing.name.lower() != item.name.lower()]
    remaining.append(item)
    return tuple(remaining)


def _upsert_many(items: tuple[Any, ...], replacements: tuple[Any, ...], *, key) -> tuple[Any, ...]:
    updated = list(items)
    for replacement in replacements:
        updated = [existing for existing in updated if key(existing) != key(replacement)]
        updated.append(replacement)
    return tuple(updated)


def _upsert_relationship(items: tuple[EntityRelationship, ...], item: EntityRelationship) -> tuple[EntityRelationship, ...]:
    remaining = [
        existing
        for existing in items
        if (existing.source_entity.lower(), existing.target_entity.lower(), existing.relation_type.lower())
        != (item.source_entity.lower(), item.target_entity.lower(), item.relation_type.lower())
    ]
    remaining.append(item)
    return tuple(remaining)


def _upsert_migration(items: tuple[SchemaMigrationRecord, ...], item: SchemaMigrationRecord) -> tuple[SchemaMigrationRecord, ...]:
    remaining = [existing for existing in items if existing.id.lower() != item.id.lower()]
    remaining.append(item)
    return tuple(remaining)


def _upsert_lineage(items: tuple[DataLineageRecord, ...], item: DataLineageRecord) -> tuple[DataLineageRecord, ...]:
    remaining = [existing for existing in items if existing.id.lower() != item.id.lower()]
    remaining.append(item)
    return tuple(remaining)


__all__ = [
    "DEFAULT_METADATA_PATH",
    "DataLineageRecord",
    "DataProductPackage",
    "EnterpriseMetadataRepository",
    "EnterpriseMetadataRepositoryError",
    "EntityMetadata",
    "EntityRelationship",
    "SchemaMigrationRecord",
    "build_default_metadata_repository",
]
