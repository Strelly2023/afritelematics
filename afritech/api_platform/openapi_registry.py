"""OpenAPI registry helpers for product API documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .endpoint_registry import EndpointRegistry


@dataclass
class OpenApiRegistry:
    registry: EndpointRegistry
    documents: dict[str, dict[str, Any]] = field(default_factory=dict)

    def build_product_document(self, product_code: str) -> dict[str, Any]:
        endpoints = self.registry.list_product(product_code)
        paths: dict[str, Any] = {}
        for endpoint in endpoints:
            path_item = paths.setdefault(endpoint.definition.path, {})
            for method in endpoint.definition.methods:
                path_item[method.lower()] = {
                    "operationId": endpoint.definition.operation_id,
                    "summary": endpoint.definition.summary,
                    "description": endpoint.definition.description,
                    "tags": list(endpoint.definition.tags),
                    "deprecated": endpoint.definition.deprecated,
                }
        document = {"openapi": "3.1.0", "info": {"title": f"{product_code} API", "version": endpoints[0].definition.version if endpoints else "v1"}, "paths": paths}
        self.documents[product_code] = document
        return document

    def build_platform_document(self) -> dict[str, Any]:
        return {
            "openapi": "3.1.0",
            "info": {"title": "NovaTech APIs", "version": "1.0.0"},
            "paths": {record.definition.path: {method.lower(): {"operationId": record.definition.operation_id} for method in record.definition.methods} for record in self.registry.list_all()},
        }
