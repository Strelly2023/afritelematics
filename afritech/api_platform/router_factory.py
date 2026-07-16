"""Router factory for governed NovaTech product APIs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Request

from .contracts import ApiEndpointDefinition, NovaTechProductApi
from .endpoint_registry import EndpointRegistry
from .execution_pipeline import ApiExecutionPipeline


class ProductRouterFactory:
    def __init__(self, execution_pipeline: ApiExecutionPipeline | None = None, endpoint_registry: EndpointRegistry | None = None) -> None:
        self.execution_pipeline = execution_pipeline or ApiExecutionPipeline()
        self.endpoint_registry = endpoint_registry or EndpointRegistry()

    def build_router(self, product_api: NovaTechProductApi) -> APIRouter:
        router = APIRouter(prefix=product_api.api_prefix, tags=[product_api.product_code])
        self.endpoint_registry.register_product_api(product_api)
        for definition in product_api.endpoint_definitions():
            self._register_endpoint(router, product_api, definition)
        return router

    def _register_endpoint(self, router: APIRouter, product_api: NovaTechProductApi, definition: ApiEndpointDefinition) -> None:
        route_path = definition.path
        if route_path.startswith(product_api.api_prefix):
            route_path = route_path[len(product_api.api_prefix) :] or "/"

        async def generated_endpoint(request: Request) -> Any:
            payload: Mapping[str, Any]
            if request.method.upper() in {"GET", "DELETE"}:
                payload = dict(request.query_params)
            else:
                try:
                    body = await request.json()
                except Exception:
                    body = {}
                payload = body if isinstance(body, Mapping) else {"value": body}
            context = request.app.state.api_platform_request_context_factory(product_api.product_code, request) if hasattr(request.app.state, "api_platform_request_context_factory") else None
            if context is None:
                from .request_context import RequestContext

                context = RequestContext.from_headers(product_api.product_code, request.headers, audience=definition.audience)
            if definition.idempotency_required and "Idempotency-Key" in request.headers:
                context = RequestContext(
                    **{**context.canonical_dict(), "extra": {**context.extra, "idempotency_key": request.headers["Idempotency-Key"]}},
                )
            result = await self.execution_pipeline.execute(
                definition=definition,
                payload=payload,
                context=context,
                product_api=product_api,
            )
            return asdict(result)

        router.add_api_route(
            route_path,
            generated_endpoint,
            methods=list(definition.methods),
            operation_id=definition.operation_id,
            summary=definition.summary,
            description=definition.description,
            tags=list(definition.tags),
            deprecated=definition.deprecated,
        )
