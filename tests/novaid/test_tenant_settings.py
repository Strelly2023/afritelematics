from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from afritech.novaid.domain import (
    Tenant,
    TenantSettings,
    TenantStatus,
)


def test_default_tenant_settings_are_secure() -> None:
    settings = TenantSettings()

    assert settings.self_registration_enabled is False
    assert settings.identity_verification_required is True
    assert settings.passkeys_enabled is True
    assert settings.federation_enabled is False
    assert settings.scim_enabled is False
    assert settings.api_access_enabled is True
    assert settings.audit_retention_days == 2555
    assert settings.default_language == "en"
    assert settings.supported_languages == (
        "en",
        "fr",
        "sw",
    )
    assert settings.feature_flags == frozenset()


def test_tenant_settings_normalize_languages() -> None:
    settings = TenantSettings(
        default_language=" FR ",
        supported_languages=(
            " EN ",
            "FR",
            " sw ",
            "fr",
        ),
    )

    assert settings.default_language == "fr"
    assert settings.supported_languages == (
        "en",
        "fr",
        "sw",
    )


def test_tenant_settings_normalize_feature_flags() -> None:
    settings = TenantSettings(
        feature_flags=frozenset(
            {
                " NovaID ",
                "NOVAPAY",
                " novaRide ",
                "",
                "   ",
            }
        ),
    )

    assert settings.feature_flags == frozenset(
        {
            "novaid",
            "novapay",
            "novaride",
        }
    )


def test_tenant_settings_support_language_lookup() -> None:
    settings = TenantSettings(
        supported_languages=(
            "en",
            "fr",
            "sw",
        ),
    )

    assert settings.supports_language("FR") is True
    assert settings.supports_language(" sw ") is True
    assert settings.supports_language("de") is False
    assert settings.supports_language("   ") is False


def test_tenant_settings_support_feature_lookup() -> None:
    settings = TenantSettings(
        feature_flags=frozenset(
            {
                "novaid",
                "novapay",
            }
        ),
    )

    assert settings.feature_enabled("NovaID") is True
    assert settings.feature_enabled(" NOVAPAY ") is True
    assert settings.feature_enabled("novaride") is False
    assert settings.feature_enabled("   ") is False


def test_default_language_must_be_supported() -> None:
    with pytest.raises(
        ValueError,
        match="TENANT_DEFAULT_LANGUAGE_NOT_SUPPORTED",
    ):
        TenantSettings(
            default_language="fr",
            supported_languages=("en", "sw"),
        )


@pytest.mark.parametrize(
    "supported_languages",
    [
        (),
        ("",),
        ("   ",),
        ("", "   "),
    ],
)
def test_supported_languages_cannot_be_empty(
    supported_languages: tuple[str, ...],
) -> None:
    with pytest.raises(
        ValueError,
        match="TENANT_SUPPORTED_LANGUAGE_REQUIRED",
    ):
        TenantSettings(
            supported_languages=supported_languages,
        )


@pytest.mark.parametrize(
    "retention_days",
    [
        0,
        -1,
        -365,
    ],
)
def test_invalid_audit_retention_is_rejected(
    retention_days: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="INVALID_AUDIT_RETENTION_DAYS",
    ):
        TenantSettings(
            audit_retention_days=retention_days,
        )


def test_tenant_settings_are_immutable() -> None:
    settings = TenantSettings()

    with pytest.raises(FrozenInstanceError):
        settings.passkeys_enabled = False  # type: ignore[misc]


def test_tenant_uses_secure_default_settings() -> None:
    tenant = Tenant(
        tenant_id="tenant-default-settings",
        name="Default Settings Tenant",
    )

    assert isinstance(
        tenant.settings,
        TenantSettings,
    )
    assert tenant.settings.identity_verification_required is True
    assert tenant.settings.self_registration_enabled is False
    assert tenant.settings.passkeys_enabled is True


def test_tenant_accepts_custom_settings() -> None:
    settings = TenantSettings(
        self_registration_enabled=True,
        federation_enabled=True,
        scim_enabled=True,
        default_language="fr",
        supported_languages=(
            "en",
            "fr",
            "sw",
        ),
        feature_flags=frozenset(
            {
                "novaid",
                "novapay",
                "novaride",
            }
        ),
    )

    tenant = Tenant(
        tenant_id="tenant-custom-settings",
        name="Custom Settings Tenant",
        settings=settings,
    )

    assert tenant.settings is settings
    assert tenant.settings.self_registration_enabled is True
    assert tenant.settings.federation_enabled is True
    assert tenant.settings.scim_enabled is True
    assert tenant.settings.default_language == "fr"


def test_tenant_transition_preserves_settings() -> None:
    settings = TenantSettings(
        federation_enabled=True,
        feature_flags=frozenset(
            {
                "novaid",
                "novapay",
            }
        ),
    )

    tenant = Tenant(
        tenant_id="tenant-settings-transition",
        name="Settings Transition Tenant",
        settings=settings,
    )

    suspended = tenant.transition(
        TenantStatus.SUSPENDED,
    )

    assert suspended.settings is settings
    assert suspended.version == tenant.version + 1
    assert suspended.status is TenantStatus.SUSPENDED
