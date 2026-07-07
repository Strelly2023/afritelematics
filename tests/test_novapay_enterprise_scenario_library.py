from __future__ import annotations

from pathlib import Path

from tests._ts_loader import ROOT, load_ts_exports, run_ts_query


DOC = ROOT / "docs/architecture/NOVAPAY_ENTERPRISE_SCENARIO_LIBRARY_2026.md"


def test_all_domain_catalogs_exist_and_are_loaded() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/scenario-engine/index.ts")
    catalogs = exported["scenarioDomainCatalogs"]
    expected_domains = [
        "Consumer Remittance",
        "Wallet Operations",
        "Merchant Payments",
        "Business Payments",
        "Agent Banking",
        "Cards",
        "Savings & Investments",
        "Lending",
        "Insurance",
        "Payroll",
        "Government Services",
        "Compliance / AML",
        "Fraud & Risk",
        "Customer Support",
        "Recovery & Disaster",
        "API / Integration Testing",
    ]
    assert sorted(catalogs.keys()) == sorted(expected_domains)


def test_total_scenario_count_and_domain_coverage() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/scenario-engine/index.ts")
    summary = exported["scenarioLibrarySummary"]
    assert summary["total"] == 790
    assert summary["domains"] == {
        "Consumer Remittance": 100,
        "Wallet Operations": 60,
        "Merchant Payments": 50,
        "Business Payments": 50,
        "Agent Banking": 40,
        "Cards": 40,
        "Savings & Investments": 30,
        "Lending": 30,
        "Insurance": 30,
        "Payroll": 30,
        "Government Services": 40,
        "Compliance / AML": 60,
        "Fraud & Risk": 60,
        "Customer Support": 40,
        "Recovery & Disaster": 30,
        "API / Integration Testing": 100,
    }


def test_every_scenario_has_required_fields_and_unique_ids() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/scenario-engine/index.ts")
    catalog = exported["scenarioCatalog"]
    seen_ids: set[str] = set()
    for scenario in catalog:
        for field in [
            "scenarioId",
            "domain",
            "title",
            "actors",
            "productsUsed",
            "sharedServicesUsed",
            "primaryProductOwner",
            "userStory",
            "preconditions",
            "workflowSteps",
            "expectedOutcome",
            "evidenceRequired",
            "policyChecks",
            "uiSurfaces",
            "apiSurfaces",
            "testType",
            "riskLevel",
            "complianceTags",
            "independenceRule",
        ]:
            assert field in scenario
        assert scenario["scenarioId"] not in seen_ids
        seen_ids.add(scenario["scenarioId"])
        assert scenario["evidenceRequired"]
        assert scenario["policyChecks"]
        assert scenario["independenceRule"]
        assert "NovaRide" not in scenario["productsUsed"]


def test_novai_is_advisory_only_and_novaride_is_not_required() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/scenario-engine/index.ts")
    catalog = exported["scenarioCatalog"]
    advisory_scenarios = [scenario for scenario in catalog if "NovaAI" in scenario["sharedServicesUsed"]]
    assert advisory_scenarios
    for scenario in advisory_scenarios:
        assert any("advisory only" in check.lower() for check in scenario["policyChecks"])
        assert scenario["primaryProductOwner"] != "NovaAI"
        assert "NovaRide" not in scenario["productsUsed"]


def test_validator_reports_no_issues() -> None:
    issues = run_ts_query(
        "packages/novatech-platform-sdk/src/scenario-engine/index.ts",
        "exported.validateScenarioCatalog(exported.scenarioCatalog)",
    )
    assert issues == []


def test_docs_exist() -> None:
    text = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaPay Enterprise Scenario Library 2026",
        "Why The Library Exists",
        "Product Boundaries",
        "Scenario Schema",
        "QA Usage",
        "UAT Usage",
        "Compliance Usage",
        "API Testing Usage",
        "Training Usage",
        "Demo Usage",
        "How Not To Duplicate App Logic",
        "Total structured scenarios: 790",
    ]:
        assert marker in text
