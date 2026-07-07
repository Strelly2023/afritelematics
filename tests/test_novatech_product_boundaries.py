from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

NOVAID_APPS = [
    "novaid_personal_app",
    "novaid_business_app",
    "novaid_employee_app",
    "novaid_partner_app",
    "novaid_inspector_app",
]
NOVAPAY_APPS = [
    "novapay_consumer_app",
    "novapay_agent_app",
    "novapay_merchant_app",
    "novapay_business_app",
]
NOVARIDE_APPS = [
    "rider_app",
    "driver_app",
    "novaride_operator_app",
    "novaride_fleet_app",
]
SHARED_PACKAGES = [
    "novatech-design-system",
    "novatech-platform-sdk",
    "novapay-core",
    "novapay-ui",
    "novaride-core",
    "novaride-ui",
]


def read_sources(root: Path) -> str:
    chunks: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "build", "dist", ".gradle", ".expo"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".ts", ".tsx", ".py", ".js", ".jsx"}:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def import_targets(source: str) -> set[str]:
    pattern = re.compile(r"(?:from\s+|import\s*\(?\s*)[\"']([^\"']+)[\"']")
    return {match.group(1) for match in pattern.finditer(source)}


def assert_no_imports(app_dirs: list[str], forbidden_markers: tuple[str, ...]) -> None:
    offenders: list[str] = []
    for directory in app_dirs:
        imports = import_targets(read_sources(ROOT / directory))
        for target in imports:
            if any(marker in target for marker in forbidden_markers):
                offenders.append(f"{directory} -> {target}")
    assert offenders == []


def test_novaid_source_does_not_import_novapay_or_novaride_app_internals() -> None:
    assert_no_imports(NOVAID_APPS, ("novapay_", "novaride_", "rider_app", "driver_app"))


def test_novapay_source_does_not_import_novaride_app_internals() -> None:
    assert_no_imports(NOVAPAY_APPS, ("novaride_", "rider_app", "driver_app"))


def test_novaride_source_uses_novapay_only_through_approved_contracts() -> None:
    offenders: list[str] = []
    approved = ("novatech-platform-sdk", "novapay-", "NovaPay")
    for directory in NOVARIDE_APPS:
        imports = import_targets(read_sources(ROOT / directory))
        for target in imports:
            if "novapay_" in target or "novapay/" in target:
                offenders.append(f"{directory} -> {target}")
            if "novapay" in target.lower() and not any(token in target for token in approved):
                offenders.append(f"{directory} -> {target}")
    assert offenders == []


def test_app_specific_business_logic_remains_in_product_apps_and_packages() -> None:
    expectations = {
        "novaid_personal_app/src/services/novaid.service.ts": ["beginVerificationFlow", "createMockIdentityProfile"],
        "packages/novapay-core/src/index.ts": ["Wallet", "Ledger", "DigitalReceipt"],
        "packages/novaride-core/src/index.ts": ["RideRequest", "RideLifecycle", "RideReceipt"],
    }
    for relative, markers in expectations.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in source


def test_shared_packages_do_not_import_product_app_internals() -> None:
    offenders: list[str] = []
    forbidden = (*NOVAID_APPS, *NOVAPAY_APPS, *NOVARIDE_APPS)
    for package in SHARED_PACKAGES:
        package_root = ROOT / "packages" / package
        if not package_root.exists():
            continue
        imports = import_targets(read_sources(package_root))
        for target in imports:
            if any(app in target for app in forbidden):
                offenders.append(f"{package} -> {target}")
    assert offenders == []


def test_novaai_is_advisory_only() -> None:
    source = (ROOT / "packages/novatech-platform-sdk/src/index.ts").read_text(encoding="utf-8")
    docs = (ROOT / "docs/architecture/NOVATECH_INTEGRATION_CONTRACTS_2026.md").read_text(encoding="utf-8")
    assert "advisoryOnly: true" in source
    assert "dispatch_ride" in source
    assert "approve_payment" in source
    assert "approve_identity" in source
    assert "NovaAI cannot dispatch rides" in docs
    assert "NovaAI cannot approve payments" in docs
    assert "NovaAI cannot approve identity" in docs


def test_product_boundary_and_integration_contract_docs_exist() -> None:
    boundary = ROOT / "docs/architecture/NOVATECH_PRODUCT_BOUNDARIES_2026.md"
    contracts = ROOT / "docs/architecture/NOVATECH_INTEGRATION_CONTRACTS_2026.md"
    assert boundary.is_file()
    assert contracts.is_file()
    boundary_text = boundary.read_text(encoding="utf-8")
    contracts_text = contracts.read_text(encoding="utf-8")
    for marker in ["NovaID Responsibilities", "NovaPay Responsibilities", "NovaRide Responsibilities", "Forbidden Coupling Rules"]:
        assert marker in boundary_text
    for marker in ["NovaID To NovaPay", "NovaPay To NovaRide", "Notification Hub", "NovaAI Advisory-Only"]:
        assert marker in contracts_text
