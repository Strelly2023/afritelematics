from __future__ import annotations

from dataclasses import replace

import pytest

from afritech.platform_runtime.config import PlatformRuntimeSettings
from afritech.platform_runtime.registry import (
    BackendProductRegistration,
    PRODUCTION_PRODUCT_MODULE_BINDINGS,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
)


def _settings(environment: str) -> PlatformRuntimeSettings:
    return PlatformRuntimeSettings(
        environment=environment,
        region="AU",
    )


def _product(
    *,
    product_code: str = "novaride",
    module_name: str = "afritech.novaride_runtime.services",
) -> BackendProductRegistration:
    return BackendProductRegistration(
        product_code=product_code,
        module_name=module_name,
        version="2026.07.0",
        owner="NovaTech",
        api_prefix="/v1/novaride",
        health_path="/health",
        database_schema="novaride",
        status=ProductRegistrationStatus.APPROVED,
    )


def test_production_binding_map_is_finite_and_contains_novaride() -> None:
    assert PRODUCTION_PRODUCT_MODULE_BINDINGS["novaride"] == (
        "afritech.novaride_runtime.services"
    )
    assert len(PRODUCTION_PRODUCT_MODULE_BINDINGS) == 5


def test_production_registry_accepts_canonical_novaride_binding(tmp_path) -> None:
    registry = ProductRuntimeRegistry(
        path=tmp_path / "registry.yaml",
        settings=_settings("production"),
        products={},
    )

    result = registry.register_product(_product())

    assert result["status"] == "registered"
    assert (
        registry.products["novaride"].module_name
        == "afritech.novaride_runtime.services"
    )


def test_production_registry_rejects_module_substitution_before_mutation(
    tmp_path,
) -> None:
    registry = ProductRuntimeRegistry(
        path=tmp_path / "registry.yaml",
        settings=_settings("production"),
        products={},
    )

    with pytest.raises(
        RuntimeError,
        match=r"^production_product_module_mismatch:",
    ):
        registry.register_product(
            _product(
                module_name=(
                    "afritech.novaride_runtime."
                    "arbitrary_runtime_plugin"
                )
            )
        )

    assert registry.products == {}
    assert not (tmp_path / "registry.yaml").exists()


def test_production_registry_rejects_unknown_product_before_mutation(
    tmp_path,
) -> None:
    registry = ProductRuntimeRegistry(
        path=tmp_path / "registry.yaml",
        settings=_settings("production"),
        products={},
    )

    with pytest.raises(
        RuntimeError,
        match=r"^production_product_not_allowlisted:",
    ):
        registry.register_product(
            _product(
                product_code="unknown_product",
                module_name="afritech.products.unknown_product",
            )
        )

    assert registry.products == {}


def test_production_constructor_rejects_external_registry_module_drift(
    tmp_path,
) -> None:
    product = _product(
        module_name=(
            "afritech.novaride_runtime."
            "runtime_substitution"
        )
    )

    with pytest.raises(
        RuntimeError,
        match=r"^production_product_module_mismatch:",
    ):
        ProductRuntimeRegistry(
            path=tmp_path / "registry.yaml",
            settings=_settings("production"),
            products={"novaride": product},
        )


def test_nonproduction_registry_retains_extensibility(tmp_path) -> None:
    registry = ProductRuntimeRegistry(
        path=tmp_path / "registry.yaml",
        settings=_settings("development"),
        products={},
    )

    custom = _product(
        product_code="experimental",
        module_name="afritech.products.experimental",
    )

    result = registry.register_product(custom)

    assert result["status"] == "registered"
    assert registry.products["experimental"] == custom
