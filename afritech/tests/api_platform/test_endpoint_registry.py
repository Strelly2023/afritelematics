from __future__ import annotations

import pytest

from afritech.api_platform import ApiEndpointDefinition, EndpointRegistry
from afritech.api_platform.errors import ApiRouteConflict


def test_endpoint_registry_rejects_duplicate_and_protected_routes() -> None:
    registry = EndpointRegistry()
    definition = ApiEndpointDefinition(
        endpoint_id="novafleet.register-vehicle.v1",
        product_code="novafleet",
        path="/v1/novafleet/vehicles",
        methods=("POST",),
        version="v1",
        operation_id="registerFleetVehicle",
        summary="Register fleet vehicle",
        description="",
        audience="CUSTOMER",
        visibility="public_authenticated",
        authentication_required=True,
        required_permissions=("novafleet:vehicle:create",),
        idempotency_required=True,
        request_schema="FleetVehicleRegistrationV1",
        response_schema="FleetVehicleResponseV1",
        metadata={"api_prefix": "/v1/novafleet"},
    )
    registry.register(definition)

    with pytest.raises(ApiRouteConflict):
        registry.register(definition)

    with pytest.raises(ApiRouteConflict):
        registry.register(
            ApiEndpointDefinition(
                endpoint_id="novafleet.platform-route",
                product_code="novafleet",
                path="/v1/platform/runtime",
                methods=("GET",),
                version="v1",
                operation_id="platformRoute",
                summary="",
                description="",
                audience="ADMIN",
                visibility="internal",
                authentication_required=True,
                metadata={"api_prefix": "/v1/novafleet"},
            )
        )

