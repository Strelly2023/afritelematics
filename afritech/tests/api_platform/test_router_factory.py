from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api_platform import ApiEndpointDefinition, ApiExecutionPipeline, EndpointRegistry, ProductRouterFactory


@dataclass
class _FakeProductApi:
    product_code: str = "novafleet"
    version: str = "v1"
    api_prefix: str = "/v1/novafleet"

    def endpoint_definitions(self):
        return (
            ApiEndpointDefinition(
                endpoint_id="novafleet.register-vehicle.v1",
                product_code=self.product_code,
                path="/v1/novafleet/vehicles",
                methods=("POST",),
                version=self.version,
                operation_id="registerFleetVehicle",
                summary="Register fleet vehicle",
                description="",
                audience="CUSTOMER",
                visibility="public_authenticated",
                authentication_required=True,
                required_roles=("RIDER",),
                required_permissions=("novafleet:vehicle:create",),
                command_name="RegisterFleetVehicle",
                idempotency_required=True,
                request_schema="FleetVehicleRegistrationV1",
                response_schema="FleetVehicleResponseV1",
                metadata={"api_prefix": self.api_prefix},
            ),
        )

    def command_handlers(self):
        return {
            "RegisterFleetVehicle": lambda payload, context: {
                "vehicle_id": payload["vehicle_id"],
                "tenant_id": context.tenant_id,
            }
        }

    def query_handlers(self):
        return {}

    def direct_handlers(self):
        return {}

    def webhooks(self):
        return ()

    def websockets(self):
        return ()


def test_router_factory_executes_governed_endpoint() -> None:
    pipeline = ApiExecutionPipeline()
    registry = EndpointRegistry()
    router = ProductRouterFactory(execution_pipeline=pipeline, endpoint_registry=registry).build_router(_FakeProductApi())
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/v1/novafleet/vehicles",
        headers={
            "x-novatech-tenant-id": "tenant-a",
            "x-novatech-organization-id": "org-a",
            "x-novatech-actor-id": "actor-a",
            "x-novatech-roles": "RIDER",
            "x-novatech-permissions": "novafleet:vehicle:create",
            "Idempotency-Key": "vehicle-1",
        },
        json={"vehicle_id": "veh-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["endpoint_id"] == "novafleet.register-vehicle.v1"
    assert body["result"]["vehicle_id"] == "veh-001"
    assert body["result"]["tenant_id"] == "tenant-a"
    assert len(pipeline.audit_recorder.events) == 1
    assert len(pipeline.evidence_store.records) == 1
    assert registry.get("novafleet.register-vehicle.v1").state == "DRAFT"

