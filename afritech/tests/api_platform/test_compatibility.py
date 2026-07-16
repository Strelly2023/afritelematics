from __future__ import annotations

from afritech.api_platform import ApiCompatibilityValidator, ApiEndpointDefinition


def test_api_compatibility_detects_breaking_changes() -> None:
    current = (
        ApiEndpointDefinition(
            endpoint_id="novafleet.register-vehicle.v1",
            product_code="novafleet",
            path="/v1/novafleet/vehicles",
            methods=("POST",),
            version="v1",
            operation_id="registerFleetVehicle",
            summary="",
            description="",
            audience="CUSTOMER",
            visibility="public_authenticated",
            authentication_required=True,
            metadata={"api_prefix": "/v1/novafleet"},
        ),
    )
    proposed = (
        ApiEndpointDefinition(
            endpoint_id="novafleet.register-vehicle.v1",
            product_code="novafleet",
            path="/v1/novafleet/fleet-vehicles",
            methods=("POST",),
            version="v1",
            operation_id="registerFleetVehicle",
            summary="",
            description="",
            audience="CUSTOMER",
            visibility="public_authenticated",
            authentication_required=True,
            metadata={"api_prefix": "/v1/novafleet"},
        ),
    )
    result = ApiCompatibilityValidator().classify(current, proposed)
    assert result.classification == "BREAKING"
    assert result.route_changes == ("novafleet.register-vehicle.v1",)

