from __future__ import annotations

from importlib import import_module

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT
from afritech.afriprogramming import control_plane
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID, PlatformStore
from afritech.architecture.novaride_architecture import (
    NOVARIDE_ARCHITECTURE_CONTRACT,
    NOVARIDE_ARCHITECTURE_REGISTRY,
    SUPPORTED_CONTRACTS,
    resolve_novaride_architecture_version,
    novaride_architecture_schema_hash,
    novaride_architecture_contract,
)

_runtime = import_module("afriride_system.api.dependencies.runtime")
reset_gateway = _runtime.reset_gateway
reset_trace_log = _runtime.reset_trace_log


def _auth_headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_novaride_api_uses_canonical_architecture_contract() -> None:
    module = import_module("afritech.api.afriride_next_gen_mobile_api")

    assert hasattr(module, "novaride_architecture_contract")
    assert not hasattr(module, "NOVARIDE_LAYERED_ARCHITECTURE")
    assert not hasattr(module, "NOVARIDE_OPERATOR_INTERVENTION_FLOW")
    assert not hasattr(module, "NOVARIDE_ENTERPRISE_OPERATIONS_LAYER")
    assert not hasattr(module, "NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS")


def test_novaride_architecture_contract_is_cached_copy_and_semantic_versioned() -> None:
    first = novaride_architecture_contract()
    second = novaride_architecture_contract()

    assert first == NOVARIDE_ARCHITECTURE_CONTRACT
    assert second == NOVARIDE_ARCHITECTURE_CONTRACT
    assert first is not NOVARIDE_ARCHITECTURE_CONTRACT
    assert first is not second
    assert first["version"] == "2026.07.0"
    assert first["layers"]
    assert first["enterprise_operations"]
    assert first["production_readiness"]


def test_novaride_architecture_contract_mutation_does_not_leak() -> None:
    payload = novaride_architecture_contract()
    payload["layers"].append("hacked")
    payload["enterprise_operations"][0]["capabilities"].append("hacked")

    clean = novaride_architecture_contract()

    assert "hacked" not in clean["layers"]
    assert "hacked" not in clean["enterprise_operations"][0]["capabilities"]


def test_novaride_architecture_registry_resolves_current_and_alias_versions() -> None:
    assert set(SUPPORTED_CONTRACTS) == {"2026.07.0"}
    assert set(NOVARIDE_ARCHITECTURE_REGISTRY) == {"2026.07", "2026.07.0"}
    assert NOVARIDE_ARCHITECTURE_REGISTRY["2026.07"] is SUPPORTED_CONTRACTS["2026.07.0"]
    assert NOVARIDE_ARCHITECTURE_REGISTRY["2026.07.0"] is SUPPORTED_CONTRACTS["2026.07.0"]
    assert resolve_novaride_architecture_version(None) == "2026.07.0"
    assert resolve_novaride_architecture_version("2026.07") == "2026.07.0"
    assert resolve_novaride_architecture_version("2026.07.0") == "2026.07.0"
    definition = SUPPORTED_CONTRACTS["2026.07.0"]
    assert "sdk_registry" in definition.capabilities
    assert definition.sdk_records()[0]["language"] == "python"
    assert definition.migration_records()[0]["from_version"] == "2026.07"
    assert definition.metric_records()["architecture_requests_total"]["unit"] == "requests"


def test_novaride_architecture_publication_exposes_version_schema_and_metrics() -> None:
    client = TestClient(app)

    response = client.get("/v1/architecture")

    assert response.status_code == 200
    payload = response.json()
    assert payload["platform"] == "NovaRide"
    assert payload["contract"]["version"] == "2026.07.0"
    assert payload["contract"]["requested_version"] == "2026.07.0"
    assert payload["contract"]["supported_versions"] == ["2026.07", "2026.07.0"]
    assert payload["contract"]["schema_hash"] == novaride_architecture_schema_hash()
    assert payload["contract"]["schema_url"] == "/v1/architecture/schema"
    assert payload["contract"]["canonical_format"] == "canonical.v1"
    assert payload["contract"]["hash_algorithm"] == "sha256"
    assert payload["contract"]["canonicalization"] == {"algorithm": "canonical.v1", "hash": "sha256"}
    assert payload["contract"]["lifecycle"]["status"] == "stable"
    assert payload["contract"]["lifecycle"]["supported_until"] == "2027-07-01"
    assert payload["contract"]["lifecycle"]["deprecation"] is None
    assert "sdk_registry" in payload["contract"]["capabilities"]
    assert payload["architecture"] == novaride_architecture_contract()
    assert "novaride_architecture_contract_version_total" in payload["observability"]["metrics"]


def test_novaride_architecture_publication_accepts_compatible_version_header() -> None:
    client = TestClient(app)

    response = client.get("/v1/architecture", headers={"X-NovaRide-Architecture": " 2026.07 "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["requested_version"] == "2026.07"
    assert payload["contract"]["version"] == "2026.07.0"
    assert payload["contract"]["compatibility"]["compatibility"] == "backward_compatible"
    assert payload["contract"]["compatibility"]["breaking_change"] is False


def test_novaride_architecture_publication_accepts_alternate_version_header() -> None:
    client = TestClient(app)

    response = client.get("/v1/architecture", headers={"Accept-Architecture-Version": "2026.07"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract"]["requested_version"] == "2026.07"
    assert payload["contract"]["version"] == "2026.07.0"


def test_novaride_architecture_publication_rejects_unsupported_version_header() -> None:
    client = TestClient(app)

    response = client.get("/v1/architecture", headers={"X-NovaRide-Architecture": "2026.08"})

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "UNSUPPORTED_NOVARIDE_ARCHITECTURE_VERSION:2026.08"
    assert error["message"] == "unsupported_novaride_architecture_version:2026.08"


def test_novaride_architecture_schema_is_machine_readable_contract() -> None:
    client = TestClient(app)

    response = client.get("/v1/architecture/schema")

    assert response.status_code == 200
    payload = response.json()
    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["title"] == "NovaRide Architecture Contract"
    assert payload["properties"]["version"]["const"] == "2026.07.0"
    assert "enterprise_operations" in payload["required"]
    assert "production_readiness" in payload["required"]


def test_novaride_architecture_contract_platform_exposes_openapi_and_lifecycle_docs() -> None:
    client = TestClient(app)

    openapi = client.get("/v1/architecture/openapi")
    changelog = client.get("/v1/architecture/changelog")
    deprecations = client.get("/v1/architecture/deprecations")
    releases = client.get("/v1/architecture/releases")

    assert openapi.status_code == 200
    assert openapi.json()["openapi"] == "3.1.0"
    assert "/v1/architecture/verify" in openapi.json()["paths"]
    assert "/v1/architecture/verify-signature" in openapi.json()["paths"]
    assert "/v1/architecture/signature" in openapi.json()["paths"]
    assert "/v1/architecture/keys" in openapi.json()["paths"]
    assert "/v1/architecture/sdk-pipeline" in openapi.json()["paths"]
    assert "/v1/architecture/protocol-marketplace" in openapi.json()["paths"]
    assert "NovaRideArchitectureContract" in openapi.json()["components"]["schemas"]

    assert changelog.status_code == 200
    assert changelog.json()["entries"][0]["version"] == "2026.07.0"
    assert changelog.json()["entries"][0]["breaking_change"] is False

    assert deprecations.status_code == 200
    assert deprecations.json()["deprecations"][0]["status"] == "stable"
    assert deprecations.json()["deprecations"][0]["deprecation"] is None

    assert releases.status_code == 200
    release = releases.json()["releases"][0]
    assert release["version"] == "2026.07.0"
    assert release["aliases"] == ["2026.07"]
    assert release["canonicalization"] == {"algorithm": "canonical.v1", "hash": "sha256"}
    assert release["schema_hash"] == novaride_architecture_schema_hash()


def test_novaride_architecture_publication_surface_is_signed_and_verifiable() -> None:
    client = TestClient(app)

    publication = client.get("/v1/architecture/publication")
    signature = client.get("/v1/architecture/signature")
    keys = client.get("/v1/architecture/keys")
    verify_signature = client.post(
        "/v1/architecture/verify-signature",
        json={"publication": publication.json()},
    )

    assert publication.status_code == 200
    payload = publication.json()
    assert payload["signature_status"] == "signed"
    assert payload["signature_version"] == 1
    assert payload["signature"]["scheme"] == "ed25519"
    assert payload["signature"]["value"]
    assert payload["signature"]["key_id"]
    assert payload["signature"]["signed_at"] == payload["signed_payload"]["signed_at"]
    assert payload["signing"]["provider"] in {"local_ed25519", "aws_kms"}
    assert payload["signing"]["algorithm"] == "ed25519"
    assert payload["signing"]["key_id"] == payload["signature"]["key_id"]
    assert "public_key" not in payload["signing"]
    assert "payload_hash" not in payload["signing"]

    assert signature.status_code == 200
    signature_payload = signature.json()
    assert signature_payload["signature_status"] == "signed"
    assert signature_payload["signature"]["scheme"] == "ed25519"
    assert signature_payload["signature"]["key_id"] == payload["signature"]["key_id"]
    assert signature_payload["signature"]["value"] == payload["signature"]["value"]
    assert signature_payload["signature"]["signed_at"] == payload["signature"]["signed_at"]
    assert signature_payload["signed_payload"] == payload["signed_payload"]
    assert signature_payload["signed_payload"]["signed_at"] == payload["signature"]["signed_at"]

    assert keys.status_code == 200
    keys_payload = keys.json()
    assert keys_payload["platform"] == "NovaRide"
    assert keys_payload["active_key_id"] == payload["signature"]["key_id"]
    assert keys_payload["trusted_keys"]
    assert keys_payload["trusted_keys"][0]["key_id"] == payload["signature"]["key_id"]
    assert keys_payload["trusted_keys"][0]["status"] == "active"
    assert keys_payload["trusted_keys"][0]["active"] is True

    assert verify_signature.status_code == 200
    verify_payload = verify_signature.json()
    assert verify_payload["valid"] is True
    assert verify_payload["publication_valid"] is True
    assert verify_payload["signature_valid"] is True
    assert verify_payload["contract_valid"] is True


def test_novaride_api_exposes_compatibility_health_aliases() -> None:
    client = TestClient(app)

    health = client.get("/v1/health")
    live = client.get("/v1/live")
    ready = client.get("/v1/ready")

    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert live.status_code == 200
    assert live.json()["alive"] is True
    assert ready.status_code in {200, 503}
    assert "ready" in ready.json()


def test_novaride_driver_operational_routes_require_auth_and_enforce_identity_and_org(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "driver-guard.sqlite3"))
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("AFRITECH_ENV", "production")
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "driver-guard-control.sqlite3")
    reset_gateway()
    reset_trace_log()

    try:
        same_org = "org-driver-guard"
        other_org = "org-driver-foreign"
        control_plane._STORE.store_driver_presence(
            organization_id=same_org,
            driver_id="driver-1",
            status="offline",
        )
        control_plane._STORE.store_driver_presence(
            organization_id=other_org,
            driver_id="driver-2",
            status="offline",
        )

        client = TestClient(app)
        driver_headers = _auth_headers("DRIVER", "driver-1", same_org)
        other_driver_headers = _auth_headers("DRIVER", "driver-2", same_org)
        operator_headers = _auth_headers("OPERATOR", "operator-1", same_org)
        fleet_headers = _auth_headers("FLEET_OWNER", "fleet-1", same_org)
        customer_headers = _auth_headers("CUSTOMER", "customer-1", same_org)

        assert client.get("/v1/driver/driver-1/availability").status_code == 401
        assert client.post("/v1/driver/driver-1/availability", json={"status": "available"}).status_code == 401
        assert client.put("/v1/driver/driver-1/availability", json={"status": "available"}).status_code == 401
        assert client.get("/v1/driver/driver-1/ride-queue").status_code == 401
        assert client.post(
            "/v1/driver/driver-1/location",
            json={
                "driver_id": "driver-1",
                "lat": -37.81,
                "lng": 144.96,
                "timestamp": "2026-07-10T00:00:00Z",
            },
        ).status_code == 401

        self_online = client.post(
            "/v1/driver/driver-1/availability",
            headers=driver_headers,
            json={"status": "available"},
        )
        assert self_online.status_code == 200
        assert self_online.json()["status"] == "available"

        self_get = client.get("/v1/driver/driver-1/availability", headers=driver_headers)
        assert self_get.status_code == 200
        assert self_get.json()["driver_id"] == "driver-1"

        cross_driver = client.get("/v1/driver/driver-1/availability", headers=other_driver_headers)
        assert cross_driver.status_code == 403
        assert cross_driver.json()["error"]["code"] == "DRIVER_IDENTITY_MISMATCH"

        org_mismatch = client.get("/v1/driver/driver-2/availability", headers=driver_headers)
        assert org_mismatch.status_code == 403
        assert org_mismatch.json()["error"]["code"] == "ORGANIZATION_ISOLATION_VIOLATION"

        wrong_role = client.get("/v1/driver/driver-1/availability", headers=customer_headers)
        assert wrong_role.status_code == 403
        assert wrong_role.json()["error"]["code"] == "DRIVER_ROLE_REQUIRED"

        operator_read = client.get("/v1/driver/driver-1/availability", headers=operator_headers)
        assert operator_read.status_code == 200
        assert operator_read.json()["driver_id"] == "driver-1"

        fleet_read = client.get("/v1/driver/driver-1/ride-queue", headers=fleet_headers)
        assert fleet_read.status_code == 200
        assert fleet_read.json()["driver_id"] == "driver-1"

        location = client.post(
            "/v1/driver/driver-1/location",
            headers=driver_headers,
            json={
                "driver_id": "driver-1",
                "lat": -37.81,
                "lng": 144.96,
                "timestamp": "2026-07-10T00:00:00Z",
            },
        )
        assert location.status_code == 200
        assert location.json()["driver_id"] == "driver-1"

        openapi = client.get("/openapi.json").json()
        availability_op = openapi["paths"]["/v1/driver/{driver_id}/availability"]["get"]
        assert availability_op["security"][0]["bearerAuth"] == []
        assert "bearerAuth" in openapi["components"]["securitySchemes"]
    finally:
        control_plane._STORE = original_store


def test_novaride_readiness_reports_valid_production_configuration_and_monitoring(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "ready.sqlite3"))
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("AFRITECH_ENV", "production")
    monkeypatch.delenv("AFRITECH_TLS_CERT_PATH", raising=False)
    monkeypatch.delenv("AFRITECH_TLS_KEY_PATH", raising=False)
    monkeypatch.delenv("AFRITECH_MIGRATION_STATE_PATH", raising=False)

    client = TestClient(app)

    ready = client.get("/v1/ready")
    metrics = client.get("/metrics")

    assert ready.status_code == 200
    payload = ready.json()
    assert payload["ready"] is True
    assert payload["configuration"] == "valid"
    assert payload["monitoring"] == "available"
    assert metrics.status_code == 200
    assert "afritech_api_ready" in metrics.text
    assert metrics.headers["content-type"].startswith("text/plain")
    assert all("valid" in item for item in payload["diagnostics"])


def test_novaride_readiness_reports_invalid_configuration_with_redacted_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "ready-invalid.sqlite3"))
    monkeypatch.setenv("AFRITECH_RUNTIME_ENVIRONMENT", "staging")
    monkeypatch.setenv("AFRITECH_ENV", "staging")

    client = TestClient(app)

    ready = client.get("/v1/ready")

    assert ready.status_code == 503
    payload = ready.json()
    assert payload["ready"] is False
    assert payload["configuration"] == "invalid"
    assert any(item["name"] == "AFRITECH_RUNTIME_ENVIRONMENT" for item in payload["diagnostics"])
    assert all("value" not in item for item in payload["diagnostics"])


def test_novaride_architecture_verify_accepts_valid_contract_hash() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/architecture/verify",
        json={
            "version": "2026.07",
            "schema_hash": novaride_architecture_schema_hash(),
            "capabilities": ["sdk_registry", "compatibility_matrix"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["canonical"] is True
    assert payload["supported"] is True
    assert payload["version"] == "2026.07"
    assert payload["resolved_version"] == "2026.07.0"
    assert payload["schema_hash_valid"] is True
    assert payload["signature_status"] == "unsigned_controlled_contract"
    assert payload["migration"] == {"required": True, "from_version": "2026.07", "to_version": "2026.07.0"}
    assert payload["capabilities"]["valid"] is True
    assert payload["capabilities"]["missing"] == []
    assert payload["capabilities_valid"] is True
    assert payload["canonicalization"] == {"algorithm": "canonical.v1", "hash": "sha256"}


def test_novaride_architecture_verify_rejects_bad_hash_and_unsupported_version() -> None:
    client = TestClient(app)

    bad_hash = client.post(
        "/v1/architecture/verify",
        json={"version": "2026.07.0", "schema_hash": "bad"},
    )
    unsupported = client.post(
        "/v1/architecture/verify",
        json={"version": "2026.08.0", "schema_hash": novaride_architecture_schema_hash()},
    )
    missing_capability = client.post(
        "/v1/architecture/verify",
        json={
            "version": "2026.07.0",
            "schema_hash": novaride_architecture_schema_hash(),
            "capabilities": ["global_consensus"],
        },
    )

    assert bad_hash.status_code == 200
    assert bad_hash.json()["valid"] is False
    assert bad_hash.json()["supported"] is True
    assert bad_hash.json()["schema_hash_valid"] is False
    assert bad_hash.json()["capabilities_valid"] is True
    assert bad_hash.json()["expected_schema_hash"] == novaride_architecture_schema_hash()

    assert unsupported.status_code == 200
    assert unsupported.json()["valid"] is False
    assert unsupported.json()["supported"] is False
    assert unsupported.json()["resolved_version"] is None
    assert unsupported.json()["signature_status"] == "unsigned_controlled_contract"
    assert unsupported.json()["capabilities_valid"] is False

    assert missing_capability.status_code == 200
    assert missing_capability.json()["valid"] is True
    assert missing_capability.json()["canonical"] is True
    assert missing_capability.json()["capabilities_valid"] is False
    assert missing_capability.json()["capabilities"]["missing"] == ["global_consensus"]


def test_novaride_architecture_ecosystem_platform_publication_surfaces() -> None:
    client = TestClient(app)

    publication = client.get("/v1/architecture/publication")
    compatibility = client.get("/v1/architecture/compatibility")
    migrations = client.get("/v1/architecture/migrations")
    sdks = client.get("/v1/architecture/sdks")
    metrics = client.get("/v1/architecture/metrics")
    ecosystem = client.get("/v1/novaride/ecosystem")
    app_store = client.get("/v1/novaride/appstore/apps")
    architecture_marketplace = client.get("/v1/architecture/protocol-marketplace")
    marketplace = client.get("/v1/novaride/developer/marketplace")

    assert publication.status_code == 200
    assert publication.json()["signature_status"] == "signed"
    assert publication.json()["signature"]["scheme"] == "ed25519"
    assert publication.json()["contract"]["schema_hash"] == novaride_architecture_schema_hash()
    assert publication.json()["contract"]["canonicalization"] == {"algorithm": "canonical.v1", "hash": "sha256"}
    assert publication.json()["signing"]["algorithm"] == "ed25519"
    assert publication.json()["signature"]["value"]
    assert publication.json()["signature"]["signed_at"] == publication.json()["signed_payload"]["signed_at"]
    assert ecosystem.status_code == 200
    assert ecosystem.json()["ecosystem_platform"]["sdk_generation_pipeline"]["steps"]
    assert ecosystem.json()["ecosystem_platform"]["app_store"]["status"] == "governed_beta"
    assert ecosystem.json()["ecosystem_platform"]["protocol_marketplace"]["status"] == "governed_beta"

    assert app_store.status_code == 200
    app_store_payload = app_store.json()
    assert app_store_payload["view"] == "novaride_app_store"
    assert app_store_payload["app_store"]["apps"][0]["name"] == "QuickDelivery"
    assert app_store_payload["app_store"]["developer_flow"][0] == "sign_up"

    assert architecture_marketplace.status_code == 200
    assert architecture_marketplace.json()["classification"] == "governed_protocol_marketplace_catalog"
    assert architecture_marketplace.json()["storefronts"][0]["name"] == "NovaRide App Store"

    assert marketplace.status_code == 200
    marketplace_payload = marketplace.json()
    assert marketplace_payload["view"] == "novaride_developer_marketplace"
    assert marketplace_payload["marketplace"]["storefronts"][0]["name"] == "NovaRide App Store"
    assert marketplace_payload["marketplace"]["developer_program"]["trust_review"] == "required"

    assert compatibility.status_code == 200
    assert {
        row["requested_version"]: row["served_version"]
        for row in compatibility.json()["matrix"]
    } == {"2026.07": "2026.07.0", "2026.07.0": "2026.07.0"}

    assert migrations.status_code == 200
    assert migrations.json()["migrations"] == [
        {
            "from_version": "2026.07",
            "to_version": "2026.07.0",
            "type": "alias_resolution",
            "breaking": False,
            "required_actions": [],
            "notes": "The compatible alias is served by the stable semantic contract.",
        }
    ]

    assert sdks.status_code == 200
    assert {target["language"] for target in sdks.json()["targets"]} == {
        "python",
        "typescript",
        "kotlin",
        "swift",
        "go",
    }
    assert sdks.json()["source"] == "/v1/architecture/openapi"

    assert app_store.status_code == 200
    assert app_store.json()["app_store"]["monetization"]["token_payment"] == "NVT_supported"

    assert metrics.status_code == 200
    assert metrics.json()["metrics"]["2026.07.0.architecture_requests_total"] == {
        "value": 0,
        "unit": "requests",
    }
    assert metrics.json()["metrics"]["2026.07.0.unsupported_contract_requests"] == {
        "value": 0,
        "unit": "requests",
    }


def test_next_gen_mobile_api_supports_rider_driver_and_operator_flows(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_DB_PATH", str(tmp_path / "next-gen-mobile.sqlite3"))
    original_store = control_plane._STORE
    control_plane._STORE = PlatformStore(tmp_path / "dashboard-analytics.sqlite3")
    reset_gateway()
    reset_trace_log()

    try:
        client = TestClient(app)

        rider_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "rider-1",
                "role": "RIDER",
                "device_id": "device-1",
                "app_version": "1.0.0",
                "platform": "ios",
            },
        )
        assert rider_session.status_code == 200
        assert rider_session.json()["actor_id"] == "rider-1"
        assert rider_session.json()["api_base_url"] == "https://api.afritechnology.com"

        rider_headers = {
            "Authorization": f"Bearer {JWT.create_token('rider-1', role='CUSTOMER', organization_id=DEFAULT_ORGANIZATION_ID)}"
        }
        rider_me = client.get("/v1/rider/me", headers=rider_headers)
        assert rider_me.status_code == 200
        rider_me_payload = rider_me.json()
        assert rider_me_payload["rider_id"] == "rider-1"
        assert rider_me_payload["role"] == "CUSTOMER"
        assert rider_me_payload["status"] == "authenticated"

        operator_session = client.post(
            "/v1/mobile/auth/session",
            json={
                "actor_id": "operator-1",
                "role": "OPERATOR",
                "device_id": "device-2",
                "app_version": "1.0.0",
                "platform": "android",
            },
        )
        assert operator_session.status_code == 200
        assert operator_session.json()["actor_id"] == "operator-1"

        driver_headers = {
            "Authorization": f"Bearer {JWT.create_token('driver-1', role='DRIVER', organization_id=DEFAULT_ORGANIZATION_ID)}"
        }
        driver_me = client.get("/v1/driver/me", headers=driver_headers)
        assert driver_me.status_code == 200
        driver_me_payload = driver_me.json()
        assert driver_me_payload["driver_id"] == "driver-1"
        assert driver_me_payload["role"] == "DRIVER"
        assert driver_me_payload["availability"]["driver_id"] == "driver-1"
        assert "ride_queue" in driver_me_payload
        assert "trip_history" in driver_me_payload

        driver_online = client.post(
            "/v1/driver/driver-1/availability",
            headers=driver_headers,
            json={"status": "available"},
        )
        assert driver_online.status_code == 200
        assert driver_online.json()["status"] == "available"
        driver_availability = client.get("/v1/driver/driver-1/availability", headers=driver_headers)
        assert driver_availability.status_code == 200
        assert driver_availability.json() == driver_online.json()
        driver_available_via_put = client.put(
            "/v1/driver/driver-1/availability",
            headers=driver_headers,
            json={"status": "available"},
        )
        assert driver_available_via_put.status_code == 200
        assert driver_available_via_put.json()["status"] == "available"

        driver_offline = client.post(
            "/v1/driver/driver-1/availability",
            headers=driver_headers,
            json={"status": "offline"},
        )
        assert driver_offline.status_code == 200
        assert driver_offline.json()["status"] == "offline"
        assert client.get("/v1/driver/driver-1/availability", headers=driver_headers).json()["status"] == "offline"

        driver_back_online = client.post(
            "/v1/driver/driver-1/availability",
            headers=driver_headers,
            json={"status": "available"},
        )
        assert driver_back_online.status_code == 200
        assert driver_back_online.json()["status"] == "available"

        requested = client.post(
            "/v1/rider/rides",
            json={
                "rider_id": "rider-1",
                "pickup": "Melbourne CBD",
                "dropoff": "Melbourne Airport",
                "pickup_lat": -37.8201,
                "pickup_lng": 144.9500,
                "ride_id": "ride-next-gen-001",
                "ride_type": "Airport",
            },
            headers={"Idempotency-Key": "ride-next-gen-request-001"},
        )
        assert requested.status_code == 200
        assert requested.json()["status"] == "requested"

        queue = client.get("/v1/driver/driver-1/ride-queue", headers=driver_headers)
        assert queue.status_code == 200
        assert queue.json()["driver_id"] == "driver-1"
        assert queue.json()["driver_status"] == "available"
        assert queue.json()["requested_count"] == 1
        assert queue.json()["items"][0]["ride_id"] == "ride-next-gen-001"

        accepted = client.post(
            "/v1/driver/rides/ride-next-gen-001/accept",
            headers=driver_headers,
            json={"driver_id": "driver-1"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["status"] == "accepted"

        location = client.post(
            "/v1/driver/driver-1/location",
            headers=driver_headers,
            json={
                "driver_id": "driver-1",
                "lat": -37.8136,
                "lng": 144.9631,
                "heading": 245,
                "timestamp": "2026-07-01T17:10:00Z",
            },
        )
        assert location.status_code == 200
        rider_tracking = client.get("/v1/rider/rides/ride-next-gen-001")
        assert rider_tracking.status_code == 200
        assert rider_tracking.json()["driver_latitude"] == -37.8136
        assert rider_tracking.json()["eta_minutes"] >= 1
        assert rider_tracking.json()["distance_km"] > 0

        arrived = client.post(
            "/v1/driver/rides/ride-next-gen-001/arrive",
            headers=driver_headers,
            json={"driver_id": "driver-1"},
        )
        assert arrived.status_code == 200
        assert arrived.json()["status"] == "arrived"

        started = client.post(
            "/v1/driver/rides/ride-next-gen-001/start",
            headers=driver_headers,
            json={"driver_id": "driver-1"},
        )
        assert started.status_code == 200
        assert started.json()["status"] == "started"

        completed = client.post(
            "/v1/driver/rides/ride-next-gen-001/complete",
            headers=driver_headers,
            json={"driver_id": "driver-1"},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "completed"

        receipt = client.get("/v1/rider/rides/ride-next-gen-001/receipt")
        assert receipt.status_code == 200
        assert receipt.json()["verification_status"] == "PASSED"

        replay = client.get("/v1/rider/rides/ride-next-gen-001/replay")
        assert replay.status_code == 200
        assert replay.json()["replay_verified"] is True

        rider_history = client.get("/v1/rider/rides/history")
        assert rider_history.status_code == 200
        assert rider_history.json()["items"][0]["ride_id"] == "ride-next-gen-001"

        operator = client.get("/v1/operator/dashboard")
        assert operator.status_code == 200
        payload = operator.json()
        assert "fleet_trust_score" in payload
        assert "driver_trust_trend" in payload
        assert "public_verification" in payload

        analytics = client.get("/v1/operator/analytics")
        assert analytics.status_code == 200
        analytics_payload = analytics.json()
        assert analytics_payload["history"]["count"] >= 1
        assert analytics_payload["latest"]["source"] == "afriride_operator_dashboard"
        assert analytics_payload["prediction"]["risk_level"] in {"low", "medium", "high"}
        assert analytics_payload["insights"]

        analytics_history = client.get("/v1/operator/analytics/history")
        assert analytics_history.status_code == 200
        assert analytics_history.json()["history"]["count"] >= 1

        analytics_prediction = client.get("/v1/operator/analytics/predictions")
        assert analytics_prediction.status_code == 200
        assert analytics_prediction.json()["prediction"]["headline"]

        operator_decisions = client.get(
            "/v1/operator/decisions",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_decisions.status_code == 200
        operator_decisions_payload = operator_decisions.json()
        assert operator_decisions_payload["current"]["decision_lane"] in {
            "observe",
            "watch",
            "review",
            "escalate",
        }
        assert operator_decisions_payload["history"]["count"] >= 1

        operator_decisions_history = client.get(
            "/v1/operator/decisions/history",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_decisions_history.status_code == 200
        assert operator_decisions_history.json()["history"]["count"] >= 1

        operator_actions = client.get(
            "/v1/operator/actions",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_actions.status_code == 200
        operator_actions_payload = operator_actions.json()
        assert operator_actions_payload["current"]["quality_band"] in {
            "excellent",
            "strong",
            "guarded",
            "weak",
            "unknown",
        }
        assert operator_actions_payload["current"]["advisory_only"] is True
        assert operator_actions_payload["current"]["execution_tier"] in {
            "advisory",
            "assisted",
            "controlled",
            "supervised",
        }
        assert "execution_tier_ready" in operator_actions_payload["current"]

        operator_actions_history = client.get(
            "/v1/operator/actions/history",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_actions_history.status_code == 200
        assert operator_actions_history.json()["history"]["count"] >= 1

        operator_autonomy = client.get(
            "/v1/operator/autonomy",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert operator_autonomy.status_code == 200
        operator_autonomy_payload = operator_autonomy.json()
        assert operator_autonomy_payload["autonomy"]["mode"] in {
            "advisory",
            "supervised",
            "autonomous",
            "fully_autonomous",
        }
        assert "safe_to_autorun" in operator_autonomy_payload["autonomy"]
        assert "thresholds" in operator_autonomy_payload["autonomy"]
        assert "driver_allocation" in operator_autonomy_payload
        assert "candidate_drivers" in operator_autonomy_payload["driver_allocation"]

        city_automation = client.get(
            "/v1/operator/city-automation",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert city_automation.status_code == 200
        city_automation_payload = city_automation.json()
        assert city_automation_payload["city_automation"]["mode"] in {
            "city_held",
            "city_supervised",
            "city_autonomous",
            "zero_operator",
        }
        assert "zero_operator_mode" in city_automation_payload["city_automation"]
        assert "coverage_score" in city_automation_payload["city_automation"]

        multi_city = client.get(
            "/v1/operator/multi-city-orchestration",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert multi_city.status_code == 200
        multi_city_payload = multi_city.json()
        assert multi_city_payload["multi_city_orchestration"]["mode"] in {
            "global_held",
            "global_supervised",
            "global_autonomous",
            "global_zero_operator",
        }
        assert "global_learning" in multi_city_payload
        assert "city_count" in multi_city_payload["multi_city_orchestration"]

        digital_twin = client.get(
            "/v1/operator/digital-twin",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert digital_twin.status_code == 200
        digital_twin_payload = digital_twin.json()
        assert digital_twin_payload["digital_twin"]["mode"] in {
            "shadow_sync",
            "predictive_closed_loop",
            "city_closed_loop",
            "global_closed_loop",
        }
        assert "self_improving_loop" in digital_twin_payload
        assert "live_sync_score" in digital_twin_payload["digital_twin"]

        business_pricing = client.get(
            "/v1/operator/business-pricing",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert business_pricing.status_code == 200
        business_pricing_payload = business_pricing.json()
        assert business_pricing_payload["view"] == "novatech_business_pricing"
        assert "pricing" in business_pricing_payload
        assert "incentives" in business_pricing_payload

        city_profit_optimization = client.get(
            "/v1/operator/city-profit-optimization",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert city_profit_optimization.status_code == 200
        city_profit_payload = city_profit_optimization.json()
        assert city_profit_payload["view"] == "novatech_city_profit_optimization"
        assert "budget_allocation" in city_profit_payload
        assert "profit_optimization" in city_profit_payload

        meta_learning = client.get(
            "/v1/operator/meta-learning-redesign",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert meta_learning.status_code == 200
        meta_learning_payload = meta_learning.json()
        assert meta_learning_payload["view"] == "novatech_meta_learning_redesign"
        assert meta_learning_payload["candidate_redesign"]["authority_boundary"] == "proposal_only"
        assert meta_learning_payload["mode"] in {"adaptive_redesign", "proposal_watch", "design_hold"}
        assert "self_redesign_rules" in meta_learning_payload
        assert "redesign_triggers" in meta_learning_payload

        intranet_analytics = client.get(
            "/v1/novatech/intranet/analytics",
            headers={"Authorization": f"Bearer {operator_session.json()['token']}"},
        )
        assert intranet_analytics.status_code == 200
        intranet_payload = intranet_analytics.json()
        assert intranet_payload["operator_analytics"]["history"]["count"] >= 1
        assert intranet_payload["novaprogramming_insights"]["status"] == "ok"
    finally:
        control_plane._STORE = original_store


def test_novaride_ecosystem_exposes_next_generation_app_family() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/ecosystem")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_ecosystem"
    assert payload["platform"] == "NovaRide"
    assert payload["app_count"] == 15
    assert payload["authority_boundary"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_boundary"]["mobile_apps"] == "request_and_observe_only"
    assert payload["lifecycle"] == [
        "passenger_requests_ride",
        "nearest_driver_matched",
        "driver_accepts",
        "driver_arrives",
        "passenger_pickup",
        "trip_in_progress",
        "destination_reached",
        "payment_via_novapay",
        "driver_settlement",
        "ratings_and_feedback",
    ]
    app_names = {app_surface["name"] for app_surface in payload["apps"]}
    assert app_names == {
        "NovaRide Passenger",
        "NovaRide Driver",
        "NovaRide Operator App / Portal",
        "NovaRide Fleet",
        "NovaRide Business",
        "NovaRide Merchant Portal",
        "NovaRide Corporate Portal",
        "NovaRide Admin",
        "NovaRide Inspector App / Portal",
        "NovaRide Trust Portal",
        "NovaRide Support",
        "NovaRide Finance Portal",
        "NovaRide Partner",
        "NovaRide Developer Portal",
        "NovaRide Executive Dashboard",
    }
    route_families = payload["route_families"]
    assert route_families["passenger"] == "/v1/novaride/passenger"
    assert route_families["partner"] == "/v1/novaride/partner"
    assert route_families["operator"] == "/v1/novaride/operator"
    assert route_families["inspector"] == "/v1/novaride/inspector"
    assert route_families["merchant"] == "/v1/novaride/merchant"
    assert route_families["corporate"] == "/v1/novaride/corporate"
    assert route_families["finance"] == "/v1/novaride/finance"
    assert route_families["developer"] == "/v1/novaride/developer"
    assert route_families["executive"] == "/v1/novaride/executive"
    assert any(service["name"] == "NovaID" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaPower" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaRide Core" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaPay" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaTrust" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaAI" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaData" for service in payload["shared_platform"])
    assert any(service["name"] == "NovaCloud" for service in payload["shared_platform"])
    assert any(service["name"] == "Audit & Replay" for service in payload["shared_platform"])
    assert any(service["name"] == "Inspection Registry" for service in payload["shared_platform"])
    assert any(service["name"] == "Incident Registry" for service in payload["shared_platform"])
    assert payload["unified_ui_framework"]["name"] == "NovaRide Unified UI Framework"
    assert payload["unified_ui_framework"]["authority_boundary"] == "ui_renders_contracts_and_recommendations_only"
    assert "ReplayTimeline" in payload["unified_ui_framework"]["shared_components"]
    assert "AgentRecommendationPanel" in payload["unified_ui_framework"]["shared_components"]
    native_surfaces = {app["surface"]: app for app in payload["native_app_activation"]}
    assert native_surfaces["passenger"]["status"] == "next_generation_active"
    assert native_surfaces["driver"]["status"] == "next_generation_active"
    assert "inspection" in native_surfaces["driver"]["required_modules"]
    agentic_modules = {module["key"]: module for module in payload["agentic_ai_modules"]}
    assert agentic_modules["demand_orchestration_agent"]["authority"] == "recommendation_only"
    assert agentic_modules["incident_triage_agent"]["authority"] == "human_approval_required"
    assert agentic_modules["finance_assurance_agent"]["authority"] == "review_required"
    canonical_architecture = novaride_architecture_contract()
    assert payload["architecture"] == canonical_architecture
    assert payload["architecture"]["version"] == "2026.07.0"
    assert payload["architecture"]["layers"]
    assert payload["architecture"]["maturity_dimensions"]
    assert payload["architecture"]["enterprise_operations"]
    assert payload["architecture"]["production_readiness"]
    architecture_apps = {app["app"] for app in payload["application_architecture"]["app_layer"]}
    assert "NovaRide Finance" in architecture_apps
    assert "NovaRide Executive Dashboard" in architecture_apps
    assert (
        payload["application_architecture"]["authority_boundary"]
        == "apps_request_and_render_backend_contracts_only"
    )
    assert (
        payload["ecosystem_platform"]["classification"]
        == "versioned_canonical_registry_backed_verification_ready_ecosystem_platform"
    )
    assert payload["ecosystem_platform"]["signed_publication"]["signature_status"] == "signed"
    assert payload["ecosystem_platform"]["signed_publication"]["signature"]["scheme"] == "ed25519"
    assert payload["ecosystem_platform"]["sdk_generation_pipeline"]["steps"]
    assert payload["ecosystem_platform"]["protocol_marketplace"]["catalog"]
    assert payload["ecosystem_platform"]["sdk_registry"]
    assert payload["ecosystem_platform"]["operational_metrics"]["2026.07.0.architecture_requests_total"] == {
        "value": 0,
        "unit": "requests",
    }
    assert payload["ecosystem_platform"]["final_score"] == {
        "platform": "NovaRide",
        "score": "10/10",
        "layers": {
            "architecture": "10/10",
            "registry": "10/10",
            "ecosystem": "10/10",
            "cryptography": "10/10",
            "trust_boundary": "10/10",
            "payload_integrity": "10/10",
        },
    }
    assert "sdk_registry" in payload["ecosystem_platform"]["capabilities"]
    assert "architecture_version" not in payload
    assert "enterprise_operations_layer" not in payload
    assert payload["enterprise_operations_score"] == "10/10"
    assert (
        payload["enterprise_operations_classification"]
        == "governed_evidence_backed_ai_assisted_mobility_control_platform"
    )
    assert "layered_architecture" not in payload
    assert "operator_intervention_flow" not in payload
    assert "maturity_dimensions" not in payload
    assert "production_infrastructure_readiness" not in payload
    assert "Demand Forecasting" in payload["intelligence_layer"]
    assert "Verification Package" in payload["trust_proof_flow"]
    assert "Control Plane decides" in payload["upgrade_principle"]


def test_novaride_platform_architecture_contract_exposes_authority_boundary_and_flow() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/platform/architecture-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_shared_platform_architecture_contract"
    assert payload["principle"] == (
        "Apps request and display; Control Plane decides; Execution Plane performs; Event Platform proves"
    )
    app_names = {app["app"] for app in payload["layers"]["app_layer"]}
    assert {
        "NovaRide Passenger",
        "NovaRide Driver",
        "NovaRide Operator Portal",
        "NovaRide Finance",
        "NovaRide Developer Portal",
        "NovaRide Executive Dashboard",
    } <= app_names
    assert payload["layers"]["api_gateway"]["role"] == "single_entry_point"
    assert payload["layers"]["api_gateway"]["responsibilities"] == [
        "request_validation",
        "novaid_authentication",
        "rbac_enforcement",
        "backend_service_routing",
    ]
    service_names = {service["name"] for service in payload["layers"]["execution_layer"]["services"]}
    assert {
        "NovaID",
        "NovaPower",
        "NovaRide Core",
        "NovaPay",
        "NovaTrust",
        "NovaAI",
        "NovaData",
        "NovaCloud",
        "Dispatch Engine",
        "Pricing Engine",
        "Maps & Routing",
        "Trust Engine",
        "NovaNotify",
        "Analytics Engine",
        "Audit & Replay",
    } <= service_names
    assert payload["authority_boundary"]["payments"] == "NovaPay_backend_only"
    assert "dispatch_decisions" in payload["authority_boundary"]["backend_full_control"]
    assert "direct_provider_access" in payload["authority_boundary"]["apps_no_authority"]
    assert payload["ride_request_flow"] == [
        "passenger_app_requests_ride",
        "api_validates_request_with_novaid",
        "pricing_engine_estimates_fare",
        "dispatch_engine_matches_driver",
        "driver_app_receives_request",
        "driver_accepts",
        "maps_tracks_trip",
        "trip_completes",
        "novapay_processes_payment",
        "audit_engine_stores_logs",
        "analytics_updated",
    ]
    matrix = {row["app"]: row["services"] for row in payload["cross_app_service_matrix"]}
    assert matrix["Partner"] == ["Dispatch", "Billing"]
    assert matrix["Support"] == ["Replay", "NovaPay"]
    assert "saas_ready_structure" in payload["strategic_outcomes"]


def test_novaride_workspace_maps_apps_to_existing_governed_routes() -> None:
    client = TestClient(app)

    passenger = client.get("/v1/novaride/passenger/workspace")
    fleet = client.get("/v1/novaride/fleet/workspace")
    inspector = client.get("/v1/novaride/inspector/workspace")
    missing = client.get("/v1/novaride/unknown/workspace")

    assert passenger.status_code == 200
    passenger_payload = passenger.json()
    assert passenger_payload["surface"]["role"] == "CUSTOMER"
    assert passenger_payload["readiness"]["backend_authority"] == "centralized"
    assert passenger_payload["readiness"]["novapay_required"] is True
    assert "/v1/rider/rides" in passenger_payload["surface"]["primary_routes"]

    assert fleet.status_code == 200
    assert fleet.json()["surface"]["role"] == "FLEET_OWNER"

    assert inspector.status_code == 200
    assert inspector.json()["surface"]["role"] == "VERIFIER"
    assert inspector.json()["readiness"]["provider_integrations"] == "backend_only"

    assert missing.status_code == 404
    assert missing.json()["error"]["message"] == "novaride_surface_not_found"


def test_novaride_operator_dashboard_contract_exposes_modules_and_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/operator/dashboard-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_operator_dashboard_contract"
    assert payload["status"] == "controlled_pilot_ready"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Operations",
        "Ride Management",
        "Driver Monitoring",
        "Safety & Emergency",
        "Analytics Dashboard",
        "Predictive Demand ML",
        "Autonomous Strategy Engine",
        "Business Pricing & Incentives",
        "Budget Allocation & Profit Optimization",
        "NovaRide Ecosystem Panel",
        "Support & Escalation",
    }
    implemented_modules = {
        module["key"]
        for module in payload["modules"]
        if module["status"] == "implemented"
    }
    assert {"analytics", "ecosystem"}.issubset(implemented_modules)
    assert "manual_dispatch" in payload["authority_model"]["allowed"]
    assert "direct_payment_execution" in payload["authority_model"]["forbidden"]
    assert payload["authority_model"]["backend_authority"]["payments"] == "NovaPay"
    assert payload["layout"]["left_navigation"] == [
        "Operations",
        "Rides",
        "Drivers",
        "Safety",
        "Analytics",
        "Support",
    ]
    assert payload["workflow"] == [
        "passenger_requests_ride",
        "dispatch_assigns_driver",
        "operator_monitors_live_map",
        "driver_delayed_operator_reassigns",
        "risk_flag_operator_intervenes",
        "trip_completed",
        "payment_processed_by_novapay",
        "operator_reviews_analytics",
    ]
    assert "/v1/operator/dashboard" in payload["api_alignment"]["implemented"]
    assert payload["api_alignment"]["contract"] == "/v1/novaride/operator/dashboard-contract"
    assert "/v1/operator/demand-forecast" in payload["api_alignment"]["implemented"]
    assert "/v1/operator/strategy-engine" in payload["api_alignment"]["implemented"]
    assert "/v1/operator/city-profit-optimization" in payload["api_alignment"]["implemented"]


def test_operator_strategy_engine_uses_default_organization(monkeypatch) -> None:
    phase5 = import_module("afritech.afriprogramming.phase5")
    captured: dict[str, object] = {}

    def build_projection(**kwargs):
        captured.update(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr(phase5, "build_autonomous_strategy_projection", build_projection)

    response = TestClient(app).get("/v1/operator/strategy-engine")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert captured == {
        "organization_id": DEFAULT_ORGANIZATION_ID,
        "source": "afriride_operator_dashboard",
        "limit": 24,
    }


def test_novaride_fleet_manager_contract_exposes_modules_rbac_and_payment_boundary() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/fleet/manager-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_fleet_manager_contract"
    assert payload["role"] == "FLEET_OWNER"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Fleet Management",
        "Driver Management",
        "Vehicle Management",
        "Maintenance & Compliance",
        "Financial Management",
        "Fleet Analytics",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Vehicles",
        "Drivers",
        "Maintenance",
        "Finance",
        "Reports",
    ]
    assert "manage_vehicles" in payload["rbac"]["allowed"]
    assert "direct_payment_provider_access" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["trust_compliance"] == "Trust_Engine_required"
    assert payload["workflow"] == [
        "fleet_adds_vehicles",
        "fleet_registers_drivers",
        "fleet_assigns_drivers_to_vehicles",
        "drivers_go_online",
        "dispatch_assigns_rides",
        "trips_completed",
        "payments_processed_via_novapay",
        "fleet_receives_earnings",
        "drivers_get_payouts",
        "fleet_monitors_analytics",
    ]
    assert "/v1/afriride/fleet/summary" in payload["api_alignment"]["implemented"]
    assert "/v1/fleet/vehicles" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "earnings_and_payouts"


def test_novaride_business_portal_contract_exposes_client_rbac_billing_and_workflow() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/business/portal-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_business_portal_contract"
    assert payload["role"] == "CLIENT"
    assert payload["sub_roles"] == ["Admin", "Manager", "Employee"]
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Corporate Travel Management",
        "Employee Management",
        "Approval Workflow",
        "Business Wallet & Billing",
        "Pricing & Incentives",
        "Budget Allocation & Profit Optimization",
        "Department Budgets",
        "Reporting & Analytics",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Employees",
        "Bookings",
        "Approvals",
        "Finance",
        "Budgets",
        "Reports",
    ]
    assert "book_rides" in payload["rbac"]["allowed"]
    assert "direct_payment_execution" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["approvals"] == "workflow_engine_required"
    assert payload["workflow"] == [
        "company_onboarded",
        "employees_added",
        "budgets_assigned",
        "employee_requests_ride",
        "approval_if_required",
        "ride_booked",
        "trip_completed",
        "novapay_processes_payment",
        "monthly_invoice_generated",
        "admin_reviews_reports",
    ]
    assert "/v1/novatech/organizations/{organization_id}/billing" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase3/business/pricing" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase3/business/incentives" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase4/business/budget-allocation" in payload["api_alignment"]["implemented"]
    assert "/v1/novaride/phase4/business/profit-optimization" in payload["api_alignment"]["implemented"]
    assert "/v1/business/approvals" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "billing_wallet_invoices"


def test_novaride_admin_contract_exposes_governance_rbac_and_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/admin/contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_admin_contract"
    assert payload["role"] == "ADMIN"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "User & Role Management",
        "Driver & Vehicle Approval",
        "Pricing & Service Configuration",
        "Geography & Service Zones",
        "Promotions & Campaigns",
        "Compliance & Audit",
        "System Health & Monitoring",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Users",
        "Drivers & Vehicles",
        "Pricing",
        "Zones",
        "Promotions",
        "Audit",
        "System",
    ]
    assert "ADMIN" in payload["rbac"]["managed_roles"]
    assert "configure_platform_rules" in payload["rbac"]["allowed"]
    assert "manual_payment_processing" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_policy_level_only"
    assert payload["authority_model"]["logs"] == "Audit_Engine_required"
    assert payload["workflow"] == [
        "driver_registers",
        "admin_reviews_documents",
        "admin_approves_driver_vehicle",
        "driver_becomes_active",
        "admin_configures_pricing",
        "admin_sets_surge_rules",
        "admin_defines_service_zones",
        "system_runs_rides_automatically",
        "novapay_processes_payments",
        "audit_logs_captured",
        "admin_monitors_system_health",
        "admin_reviews_alerts",
        "admin_adjusts_rules_if_needed",
    ]
    assert "/v1/afriride/rbac/catalog" in payload["api_alignment"]["implemented"]
    assert "/v1/admin/pricing" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "policy_level_control_only"


def test_novaride_inspector_app_contract_exposes_verifier_workflow_and_trust_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/inspector/app-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_inspector_app_contract"
    assert payload["role"] == "VERIFIER"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Inspection Workflow",
        "Driver Verification",
        "Vehicle Inspection",
        "Document Validation",
        "Photo & Evidence Capture",
        "Inspection Reports",
        "Compliance Status",
    }
    assert payload["navigation"] == ["Home", "Inspection", "Reports", "Profile"]
    status_types = {status["status"]: status["meaning"] for status in payload["status_types"]}
    assert status_types == {
        "compliant": "allowed_to_operate",
        "pending": "requires_review",
        "non_compliant": "suspended",
    }
    assert "perform_inspections" in payload["rbac"]["allowed"]
    assert "trust_engine_bypass" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["compliance"] == "Trust_Engine_final_authority"
    assert payload["authority_model"]["evidence"] == "Audit_Engine_replay_required"
    assert payload["workflow"] == [
        "inspector_logs_in",
        "selects_driver_vehicle",
        "starts_inspection",
        "completes_checklist",
        "captures_photos",
        "submits_report",
        "trust_engine_evaluates_compliance",
        "status_updated",
        "driver_approved_or_suspended",
    ]
    assert "/v1/operator/public-verification/status" in payload["api_alignment"]["implemented"]
    assert "/v1/inspector/inspections" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["trust_engine"] == "final_authority"


def test_novaride_support_contract_exposes_ticket_refund_and_replay_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/support/contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_support_contract"
    assert payload["role"] == "OPERATOR"
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Customer Ticket Management",
        "Ride Lookup & Investigation",
        "Refund & Dispute Handling",
        "Driver & Passenger Assistance",
        "Escalation Management",
        "Audit & Replay Integration",
    }
    assert payload["navigation"] == ["Tickets", "Ride Lookup", "Refunds", "Escalations", "Reports"]
    assert payload["ticket_statuses"] == ["Open", "In Progress", "Resolved", "Closed"]
    escalation_levels = {level["level"]: level["meaning"] for level in payload["escalation_levels"]}
    assert escalation_levels == {
        "level_1": "standard_support",
        "level_2": "supervisor",
        "level_3": "critical_admin",
    }
    assert "request_refunds" in payload["rbac"]["allowed"]
    assert "direct_payment_execution" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["refund_execution"] == "NovaPay_backend_only"
    assert payload["authority_model"]["ride_evidence"] == "Audit_Engine_replay_required"
    assert payload["workflow"] == [
        "passenger_raises_issue",
        "ticket_created",
        "support_agent_reviews_ride",
        "replay_trip_data",
        "verify_fare_via_pricing_engine",
        "decide_refund_or_action",
        "novapay_processes_refund",
        "ticket_closed",
    ]
    assert "/v1/operator/replay-exceptions" in payload["api_alignment"]["implemented"]
    assert "/v1/support/tickets" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "processes_refunds"


def test_novaride_partner_portal_contract_exposes_b2b_workflow_and_backend_authority() -> None:
    client = TestClient(app)

    response = client.get("/v1/novaride/partner/portal-contract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["view"] == "novaride_partner_portal_contract"
    assert payload["role"] == "PARTNER"
    assert payload["partner_types"] == [
        "airports",
        "hotels",
        "event_organizers",
        "corporations",
        "travel_agencies",
    ]
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {
        "Ride Booking & Widget Integration",
        "Guest Transport Management",
        "Bulk Ride Requests",
        "Partner Reporting",
        "Billing & Payments",
        "Partner Configuration",
    }
    assert payload["navigation"] == [
        "Dashboard",
        "Bookings",
        "Guests",
        "Tracking",
        "Reports",
        "Billing",
        "Settings",
    ]
    assert "book_guest_rides" in payload["rbac"]["allowed"]
    assert "direct_payment_processing" in payload["rbac"]["forbidden"]
    assert payload["authority_model"]["payments"] == "NovaPay_backend_only"
    assert payload["authority_model"]["dispatch"] == "Dispatch_Engine_required"
    assert payload["workflow"] == [
        "hotel_staff_logs_in",
        "books_ride_for_guest",
        "guest_receives_ride_details",
        "driver_picks_up_guest",
        "trip_completed",
        "novapay_charges_partner_account",
        "monthly_invoice_generated",
        "partner_reviews_reports",
    ]
    assert "/v1/partners/registry" in payload["api_alignment"]["implemented"]
    assert "/v1/partner/bookings" in payload["api_alignment"]["next_phase"]
    assert payload["ecosystem_integrations"]["novapay"] == "billing_and_payments"
