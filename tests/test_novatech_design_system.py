from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PRODUCT_APPS = [
    "rider_app",
    "driver_app",
    "novaride_operator_app",
    "novaride_fleet_app",
    "novapay_consumer_app",
    "novapay_agent_app",
    "novapay_merchant_app",
    "novapay_business_app",
    "novaid_personal_app",
    "novaid_business_app",
    "novaid_employee_app",
    "novaid_partner_app",
    "novaid_inspector_app",
]


def test_shared_design_system_package_exists() -> None:
    package = ROOT / "packages/novatech-design-system"
    assert (package / "package.json").is_file()
    assert (package / "src/index.ts").is_file()


def test_all_product_apps_reference_shared_design_tokens_or_primitives() -> None:
    missing: list[str] = []
    for app in PRODUCT_APPS:
        bridge = ROOT / app / "src/designSystem.ts"
        if not bridge.is_file():
            missing.append(app)
            continue
        source = bridge.read_text(encoding="utf-8")
        assert "novatech-design-system" in source
        assert "designTokens" in source
        assert "stateComponents" in source
        assert "accessibility" in source
    assert missing == []


def test_required_state_components_exist() -> None:
    source = (ROOT / "packages/novatech-design-system/src/index.ts").read_text(encoding="utf-8")
    for state in ["loading", "empty", "error", "success", "offline"]:
        assert state in source
    assert "stateComponents" in source


def test_required_cards_and_indicators_exist() -> None:
    source = (ROOT / "packages/novatech-design-system/src/index.ts").read_text(encoding="utf-8")
    for marker in [
        "trustIndicators",
        "receiptCard",
        "identityCard",
        "rideCard",
        "walletCard",
        "statusBadges",
        "cardPrimitives",
        "buttonPrimitives",
    ]:
        assert marker in source


def test_accessibility_helpers_exist() -> None:
    source = (ROOT / "packages/novatech-design-system/src/index.ts").read_text(encoding="utf-8")
    assert "WCAG 2.2" in source
    assert "minTouchTarget" in source
    assert "labelFor" in source
    assert "hintFor" in source


def test_product_ui_packages_consume_shared_tokens() -> None:
    novapay = (ROOT / "packages/novapay-ui/src/index.ts").read_text(encoding="utf-8")
    novaride = (ROOT / "packages/novaride-ui/src/index.ts").read_text(encoding="utf-8")
    assert "novatech-design-system" in novapay
    assert "NOVAPAY_SHARED_DESIGN" in novapay
    assert "novatech-design-system" in novaride
    assert "NOVARIDE_SHARED_DESIGN" in novaride
