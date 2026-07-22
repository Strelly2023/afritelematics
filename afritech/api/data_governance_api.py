"""Metadata-driven NovaTech enterprise data governance API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.data_governance.enterprise import (
    ContractStatus,
    DataContract,
    DataEventDefinition,
    DataSharingLevel,
    EnterpriseDataGovernanceError,
    ProductDataExtension,
    SchemaChangeClass,
    enterprise_data_manifest,
)
from afritech.data_governance.metadata_repository import (
    DataLineageRecord,
    EnterpriseMetadataRepository,
    EnterpriseMetadataRepositoryError,
    EntityMetadata,
    EntityRelationship,
    SchemaMigrationRecord,
    build_default_metadata_repository,
)


class ProductRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    product_code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    version: str = Field(default="2026.07.0", min_length=1)
    classification: str = Field(default="CONFIDENTIAL", min_length=1)
    region: str = Field(default="GLOBAL", min_length=1)
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    extensions: list[dict[str, Any]] = Field(default_factory=list)
    contracts: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    migrations: list[dict[str, Any]] = Field(default_factory=list)


class EntityRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    schema_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    source_of_truth: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    product_code: str = Field(min_length=1)
    version: str = Field(default="1.0.0", min_length=1)
    status: str = Field(default="ACTIVE", min_length=1)
    description: str = ""
    business_meaning: str = ""
    privacy: str = ""
    llm_visibility: str = "approved_fields_only"
    confidence: str = "high"
    fields: list[str] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)
    example_queries: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    ai_metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_entity: str = Field(min_length=1)
    target_entity: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    cardinality: str = "many_to_one"
    description: str = ""


class MigrationRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    product_code: str = Field(min_length=1)
    version: str = Field(min_length=1)
    checksum: str = Field(min_length=1)
    author: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)
    applied_at: str = Field(min_length=1)
    rollback_version: str = Field(min_length=1)
    status: str = "APPROVED"


class LineageRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    source_product: str = Field(min_length=1)
    target_product: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    path: list[str] = Field(default_factory=list)
    recorded_at: str = Field(min_length=1)
    evidence_hash: str = Field(min_length=1)
    classification: str = "CONFIDENTIAL"
    status: str = "ACTIVE"


class ContractRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    contract_id: str = Field(min_length=1)
    producer_product: str = Field(min_length=1)
    consumer_product: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    purpose: str = Field(min_length=1)
    allowed_fields: list[str] = Field(default_factory=list)
    retention_policy: str = Field(min_length=1)
    consent_required: bool = False
    status: str = "APPROVED"
    sharing_level: str = "ENTERPRISE"
    schema_change: str = "COMPATIBLE"
    classification: str = "CONFIDENTIAL"
    topic: str = ""


class EventRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_type: str = Field(min_length=1)
    event_version: int = Field(ge=1)
    producer_product: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    payload_fields: list[str] = Field(default_factory=list)
    consumers: list[str] = Field(default_factory=list)
    classification: str = Field(min_length=1)
    sharing_level: str = "ENTERPRISE"
    schema_change: str = "COMPATIBLE"
    retention_policy: str = "AUDIT"


def _repository(repository: EnterpriseMetadataRepository | None = None) -> EnterpriseMetadataRepository:
    return repository or build_default_metadata_repository()


def _contract_from_request(request: ContractRegistrationRequest) -> DataContract:
    try:
        return DataContract(
            contract_id=request.contract_id,
            producer_product=request.producer_product,
            consumer_product=request.consumer_product,
            data_type=request.data_type,
            schema_version=request.schema_version,
            purpose=request.purpose,
            allowed_fields=tuple(request.allowed_fields),
            retention_policy=request.retention_policy,
            consent_required=request.consent_required,
            status=ContractStatus(request.status),
            sharing_level=DataSharingLevel(request.sharing_level),
            schema_change=SchemaChangeClass(request.schema_change),
            classification=request.classification,
            topic=request.topic,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _event_from_request(request: EventRegistrationRequest) -> DataEventDefinition:
    try:
        return DataEventDefinition(
            event_type=request.event_type,
            event_version=request.event_version,
            producer_product=request.producer_product,
            topic=request.topic,
            payload_fields=tuple(request.payload_fields),
            consumers=tuple(request.consumers),
            classification=request.classification,
            sharing_level=DataSharingLevel(request.sharing_level),
            schema_change=SchemaChangeClass(request.schema_change),
            retention_policy=request.retention_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _entity_from_request(request: EntityRegistrationRequest) -> EntityMetadata:
    try:
        relationships = tuple(
            EntityRelationship(
                source_entity=item["source_entity"],
                target_entity=item["target_entity"],
                relation_type=item["relation_type"],
                cardinality=item.get("cardinality", "many_to_one"),
                description=item.get("description", ""),
            )
            for item in request.relationships
        )
        return EntityMetadata(
            name=request.name,
            schema_name=request.schema_name,
            owner=request.owner,
            source_of_truth=request.source_of_truth,
            classification=request.classification,
            product_code=request.product_code,
            version=request.version,
            status=request.status,
            description=request.description,
            business_meaning=request.business_meaning,
            privacy=request.privacy,
            llm_visibility=request.llm_visibility,
            confidence=request.confidence,
            fields=tuple(request.fields),
            relationships=relationships,
            indexes=tuple(request.indexes),
            example_queries=tuple(request.example_queries),
            tags=tuple(request.tags),
            ai_metadata=dict(request.ai_metadata),
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"relationship_missing_field:{exc.args[0]}") from exc


def _migration_from_request(request: MigrationRegistrationRequest) -> SchemaMigrationRecord:
    return SchemaMigrationRecord(
        id=request.id,
        product_code=request.product_code,
        version=request.version,
        checksum=request.checksum,
        author=request.author,
        approved_by=request.approved_by,
        applied_at=request.applied_at,
        rollback_version=request.rollback_version,
        status=request.status,
    )


def _lineage_from_request(request: LineageRegistrationRequest) -> DataLineageRecord:
    return DataLineageRecord(
        id=request.id,
        source_product=request.source_product,
        target_product=request.target_product,
        data_type=request.data_type,
        purpose=request.purpose,
        path=tuple(request.path),
        recorded_at=request.recorded_at,
        evidence_hash=request.evidence_hash,
        classification=request.classification,
        status=request.status,
    )


def _safe_not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "DATA_METADATA_NOT_FOUND", "message": message})


def build_data_governance_router(
    repository: EnterpriseMetadataRepository | None = None,
    *,
    include_platform_aliases: bool = True,
) -> APIRouter:
    router = APIRouter(tags=["data-governance"])
    repo = _repository(repository)

    def platform_alias(path: str, *, methods: list[str]):
        if include_platform_aliases:
            return router.api_route(path, methods=methods)

        def unchanged(endpoint):
            return endpoint

        return unchanged

    @router.get("/v1/novatech/data-governance")
    @router.get("/v1/platform/data-governance")
    async def data_governance_overview(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        model = repo.model
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "model": model.summary(),
            "shared_entities": [entity.canonical_dict() for entity in model.shared_entities],
            "product_domains": [domain.canonical_dict() for domain in model.product_domains],
            "product_extensions": [extension.canonical_dict() for extension in model.product_extensions],
            "contracts": [contract.canonical_dict() for contract in model.contracts],
            "events": [event.canonical_dict() for event in model.events],
            "dashboard": repo.get_dashboard(),
            "summary": repo.summary(),
            "manifest": enterprise_data_manifest(repo.model),
        }

    @router.get("/v1/novatech/data-governance/metadata")
    @router.get("/v1/platform/metadata")
    async def metadata_manifest(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "summary": repo.summary(),
            "manifest": enterprise_data_manifest(repo.model),
        }

    @router.get("/v1/novatech/data-governance/products")
    @platform_alias("/v1/platform/products", methods=["GET"])
    async def list_products(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "products": repo.list_products(),
        }

    @router.post("/v1/novatech/data-governance/products")
    @platform_alias("/v1/platform/products", methods=["POST"])
    async def register_product(
        payload: ProductRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        entities = tuple(_entity_from_request(EntityRegistrationRequest.model_validate(item)) for item in payload.entities)
        extensions = tuple(
            ProductDataExtension(
                product_code=item["product_code"],
                base_entity=item["base_entity"],
                table_name=item["table_name"],
                fields=tuple(item["fields"]),
                owner=item["owner"],
                classification=item.get("classification", payload.classification),
            )
            for item in payload.extensions
        )
        contracts = tuple(_contract_from_request(ContractRegistrationRequest.model_validate(item)) for item in payload.contracts)
        events = tuple(_event_from_request(EventRegistrationRequest.model_validate(item)) for item in payload.events)
        migrations = tuple(_migration_from_request(MigrationRegistrationRequest.model_validate(item)) for item in payload.migrations)
        result = repo.register_product(
            product_code=payload.product_code,
            name=payload.name,
            owner=payload.owner,
            schema_name=payload.schema_name,
            version=payload.version,
            classification=payload.classification,
            region=payload.region,
            description=payload.description,
            metadata=payload.metadata,
            entities=entities,
            extensions=extensions,
            contracts=contracts,
            events=events,
            migrations=migrations,
        )
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/products/{product_code}")
    @platform_alias("/v1/platform/products/{product_code}", methods=["GET"])
    async def get_product(
        product_code: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "product": repo.get_product(product_code),
                "entities": repo.product_entities(product_code),
            }
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/domains/{product_code}")
    @router.get("/v1/platform/domains/{product_code}")
    async def get_domain(
        product_code: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "domain": repo.model.product_domain(product_code).canonical_dict(),
                "extensions": [
                    extension.canonical_dict()
                    for extension in repo.model.product_extensions
                    if extension.product_code.lower() == product_code.strip().lower()
                ],
            }
        except EnterpriseDataGovernanceError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/entities")
    @router.get("/v1/platform/entities")
    async def list_entities(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "entities": repo.list_entities(),
        }

    @router.post("/v1/novatech/data-governance/entities")
    @router.post("/v1/platform/entities")
    async def register_entity(
        payload: EntityRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        entity = _entity_from_request(payload)
        result = repo.register_entity(entity)
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/relationships")
    @router.get("/v1/platform/relationships")
    async def list_relationships(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "relationships": repo.list_relationships(),
        }

    @router.post("/v1/novatech/data-governance/relationships")
    @router.post("/v1/platform/relationships")
    async def register_relationship(
        payload: RelationshipRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = repo.register_relationship(
            EntityRelationship(
                source_entity=payload.source_entity,
                target_entity=payload.target_entity,
                relation_type=payload.relation_type,
                cardinality=payload.cardinality,
                description=payload.description,
            )
        )
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/entities/{entity_name}")
    @router.get("/v1/platform/entities/{entity_name}")
    async def get_entity(
        entity_name: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "entity": repo.get_entity(entity_name),
            }
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/entities/{entity_name}/related")
    async def entity_relationships(
        entity_name: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            entity = repo.get_entity(entity_name)
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc
        related = [
            relationship
            for relationship in repo.list_relationships()
            if relationship["source_entity"].lower() == entity_name.lower()
            or relationship["target_entity"].lower() == entity_name.lower()
        ]
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "entity": entity,
            "relationships": related,
        }

    @router.get("/v1/novatech/data-governance/entities/{entity_name}/products")
    async def entity_products(
        entity_name: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            entity = repo.get_entity(entity_name)
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc
        product_code = str(entity.get("product_code") or entity.get("source_of_truth") or "")
        products = []
        if product_code:
            try:
                products.append(repo.get_product(product_code))
            except EnterpriseMetadataRepositoryError:
                product = next(
                    (
                        domain.canonical_dict()
                        for domain in repo.model.product_domains
                        if domain.product_code.lower() == product_code.lower()
                    ),
                    None,
                )
                if product is not None:
                    products.append(product)
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "entity": entity,
            "products": products,
        }

    @router.get("/v1/novatech/data-governance/contracts")
    @router.get("/v1/platform/contracts")
    async def list_contracts(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "contracts": repo.list_contracts(),
        }

    @router.post("/v1/novatech/data-governance/contracts")
    @router.post("/v1/platform/contracts")
    async def register_contract(
        payload: ContractRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = repo.register_contract(_contract_from_request(payload))
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/contracts/{contract_id}")
    @router.get("/v1/platform/contracts/{contract_id}")
    async def get_contract(
        contract_id: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "contract": repo.model.contract(contract_id).canonical_dict(),
            }
        except EnterpriseDataGovernanceError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/events")
    @router.get("/v1/platform/events")
    async def list_events(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "events": repo.list_events(),
        }

    @router.post("/v1/novatech/data-governance/events")
    @router.post("/v1/platform/events")
    async def register_event(
        payload: EventRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = repo.register_event(_event_from_request(payload))
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/events/{event_type}")
    @router.get("/v1/platform/events/{event_type}")
    async def get_event(
        event_type: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "event": repo.model.event(event_type).canonical_dict(),
            }
        except EnterpriseDataGovernanceError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/migrations")
    @platform_alias("/v1/platform/migrations", methods=["GET"])
    async def list_migrations(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "migrations": repo.list_migrations(),
        }

    @router.post("/v1/novatech/data-governance/migrations")
    @platform_alias("/v1/platform/migrations", methods=["POST"])
    async def register_migration(
        payload: MigrationRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = repo.register_migration(_migration_from_request(payload))
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/migrations/{migration_id}")
    @platform_alias("/v1/platform/migrations/{migration_id}", methods=["GET"])
    async def get_migration(
        migration_id: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "migration": repo.get_migration(migration_id),
            }
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/lineage")
    @router.get("/v1/platform/lineage")
    async def list_lineage(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "lineage": repo.list_lineage(),
        }

    @router.post("/v1/novatech/data-governance/lineage")
    @router.post("/v1/platform/lineage")
    async def register_lineage(
        payload: LineageRegistrationRequest,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER")),
    ) -> dict[str, Any]:
        result = repo.record_lineage(_lineage_from_request(payload))
        result["tenant_id"] = claims.tenant_id
        result["organization_id"] = claims.organization_id
        return result

    @router.get("/v1/novatech/data-governance/lineage/{lineage_id}")
    @router.get("/v1/platform/lineage/{lineage_id}")
    async def get_lineage(
        lineage_id: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "lineage": repo.get_lineage(lineage_id),
            }
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/graph")
    @router.get("/v1/platform/graph")
    async def data_graph(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        nodes = [
            {"id": entity["name"], "label": entity["name"], "type": "entity", "owner": entity["owner"]}
            for entity in repo.list_entities()
        ]
        nodes.extend(
            {"id": product["product_code"], "label": product["name"], "type": "product", "owner": product["owner"]}
            for product in repo.list_products()
        )
        nodes.extend(
            {"id": contract["contract_id"], "label": contract["data_type"], "type": "contract", "owner": contract["producer_product"]}
            for contract in repo.list_contracts()
        )
        nodes.extend(
            {"id": event["event_type"], "label": event["event_type"], "type": "event", "owner": event["producer_product"]}
            for event in repo.list_events()
        )
        edges = [
            {
                "from": relationship["source_entity"],
                "to": relationship["target_entity"],
                "type": relationship["relation_type"],
                "cardinality": relationship["cardinality"],
            }
            for relationship in repo.list_relationships()
        ]
        for contract in repo.list_contracts():
            edges.append(
                {
                    "from": contract["producer_product"],
                    "to": contract["consumer_product"],
                    "type": "contract",
                    "label": contract["contract_id"],
                }
            )
        for lineage in repo.list_lineage():
            path = lineage["path"]
            for left, right in zip(path, path[1:]):
                edges.append({"from": left, "to": right, "type": "lineage", "label": lineage["id"]})
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "nodes": nodes,
            "edges": edges,
            "acyclic": True,
        }

    @router.get("/v1/novatech/data-governance/ai-metadata")
    @router.get("/v1/platform/ai-metadata")
    async def ai_metadata(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "ai_metadata": repo.ai_metadata(),
        }

    @router.get("/v1/novatech/data-governance/search")
    @router.get("/v1/platform/search")
    async def search(
        q: str = Query(default="", alias="query"),
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "search": repo.search(q),
        }

    @router.get("/v1/novatech/data-governance/dashboard")
    @router.get("/v1/platform/dashboard")
    async def dashboard(
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "dashboard": repo.get_dashboard(),
        }

    @router.get("/v1/novatech/data-governance/products/{product_code}/entities")
    @platform_alias("/v1/platform/products/{product_code}/entities", methods=["GET"])
    async def product_entities(
        product_code: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            return {
                "platform": "NovaTech",
                "tenant_id": claims.tenant_id,
                "organization_id": claims.organization_id,
                "product_code": product_code,
                "entities": repo.product_entities(product_code),
            }
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc

    @router.get("/v1/novatech/data-governance/lineage/{lineage_id}/path")
    async def lineage_path(
        lineage_id: str,
        claims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            lineage = repo.get_lineage(lineage_id)
        except EnterpriseMetadataRepositoryError as exc:
            raise _safe_not_found(str(exc)) from exc
        return {
            "platform": "NovaTech",
            "tenant_id": claims.tenant_id,
            "organization_id": claims.organization_id,
            "lineage": lineage,
            "path": lineage["path"],
        }

    return router


__all__ = ["build_data_governance_router"]
