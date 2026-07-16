from __future__ import annotations

import importlib
from types import ModuleType

import pytest

from afritech.platform_runtime import (
    BackendProductRegistration,
    ProductContractViolation,
    ProductLoadRejected,
    ProductModuleLoader,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
)

from .conftest import build_fake_module


def test_product_loader_loads_executable_backend(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    module = build_fake_module()

    def fake_import(name: str) -> ModuleType:
        assert name == "afritech.products.novafleet"
        return module

    monkeypatch.setattr(importlib, "import_module", fake_import)

    registry = ProductRuntimeRegistry(path=tmp_path / "registry.yaml")
    registry.register_product(
        BackendProductRegistration(
            product_code="novafleet",
            module_name="afritech.products.novafleet",
            version="2026.07.0",
            owner="Fleet Team",
            api_prefix="/v1/novafleet",
            health_path="/health/products/novafleet",
            database_schema="novafleet",
            status=ProductRegistrationStatus.APPROVED,
            registered_commands=("RegisterFleetVehicle",),
            registered_queries=("GetFleetVehicle",),
            registered_workers=("fleet-worker",),
            registered_consumers=("fleet-consumer",),
            infrastructure={"postgres": "novafleet"},
            configuration={"maintenance_reminder_days": 30},
            module_version="2026.07.0",
        )
    )

    loader = ProductModuleLoader()
    loaded = loader.load(registry._require_product("novafleet"))

    assert loaded.product_code == "novafleet"
    assert loaded.state.value == "LOADED"
    assert "RegisterFleetVehicle" in loaded.commands
    assert "GetFleetVehicle" in loaded.queries
    assert loaded.routers[0].prefix == "/v1/novafleet"
    assert loaded.workers[0].queue == "novafleet.jobs"
    assert loaded.module_checksum.startswith("sha256:")


def test_product_loader_rejects_unapproved_status(tmp_path) -> None:
    registry = ProductRuntimeRegistry(path=tmp_path / "registry.yaml")
    registry.register_product(
        BackendProductRegistration(
            product_code="novafleet",
            module_name="afritech.products.novafleet",
            version="2026.07.0",
            owner="Fleet Team",
            api_prefix="/v1/novafleet",
            health_path="/health/products/novafleet",
            database_schema="novafleet",
            status=ProductRegistrationStatus.DRAFT,
        )
    )

    with pytest.raises(ProductLoadRejected, match="product_not_loadable"):
        ProductModuleLoader().load(registry._require_product("novafleet"))


def test_product_loader_rejects_disallowed_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    module = build_fake_module("evil.products.novafleet")
    monkeypatch.setattr(importlib, "import_module", lambda name: module)

    registry = ProductRuntimeRegistry(path=tmp_path / "registry.yaml")
    registry.register_product(
        BackendProductRegistration(
            product_code="novafleet",
            module_name="evil.products.novafleet",
            version="2026.07.0",
            owner="Fleet Team",
            api_prefix="/v1/novafleet",
            health_path="/health/products/novafleet",
            database_schema="novafleet",
            status=ProductRegistrationStatus.APPROVED,
        )
    )

    with pytest.raises(ProductContractViolation, match="module_prefix_not_allowed"):
        ProductModuleLoader().load(registry._require_product("novafleet"))


def test_product_loader_rejects_version_mismatch(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    module = build_fake_module()

    class VersionMismatchBackend(type(module.get_product_backend())):
        version = "2026.07.1"

    def fake_import(name: str) -> ModuleType:
        backend_module = build_fake_module()
        backend_module.get_product_backend = lambda: VersionMismatchBackend()  # type: ignore[assignment]
        return backend_module

    monkeypatch.setattr(importlib, "import_module", fake_import)

    registry = ProductRuntimeRegistry(path=tmp_path / "registry.yaml")
    registry.register_product(
        BackendProductRegistration(
            product_code="novafleet",
            module_name="afritech.products.novafleet",
            version="2026.07.0",
            owner="Fleet Team",
            api_prefix="/v1/novafleet",
            health_path="/health/products/novafleet",
            database_schema="novafleet",
            status=ProductRegistrationStatus.APPROVED,
        )
    )

    with pytest.raises(ProductContractViolation, match="version_mismatch"):
        ProductModuleLoader().load(registry._require_product("novafleet"))
