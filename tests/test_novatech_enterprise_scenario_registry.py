from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "packages/novatech-platform-sdk/src/index.ts"
DOC = ROOT / "docs/architecture/NOVATECH_ENTERPRISE_SCENARIO_REGISTRY_2026.md"


def sdk() -> str:
    return SDK.read_text(encoding="utf-8")


def test_enterprise_registry_types_exist() -> None:
    text = sdk()
    for marker in [
        "ScenarioRegistryDomain",
        "ScenarioClassification",
        "ScenarioTestSuite",
        "ScenarioEvidenceArtifact",
        "ScenarioPersona",
        "ScenarioCorridor",
        "ScenarioDomainTarget",
        "EnterpriseScenarioMetadata",
        "enterpriseScenarioRegistrySeed",
        "scenarioRegistrySummary",
    ]:
        assert marker in text


def test_registry_personas_cover_required_roles() -> None:
    text = sdk()
    for marker in [
        "First-time customer",
        "Returning customer",
        "Refugee",
        "International student",
        "Tourist",
        "Migrant worker",
        "Freelancer",
        "Small business owner",
        "Merchant",
        "Corporate finance officer",
        "NGO administrator",
        "Government officer",
        "Elderly customer",
        "Visually impaired customer",
        "Agent operator",
        "Compliance analyst",
    ]:
        assert marker in text
    assert text.count("personaId:") >= 16


def test_registry_corridors_cover_supported_launch_routes() -> None:
    text = sdk()
    for marker in [
        "Australia",
        "United States",
        "Canada",
        "United Kingdom",
        "France",
        "Belgium",
        "United Arab Emirates",
        "Saudi Arabia",
        "South Africa",
        "Nigeria",
        "DR Congo",
        "Bangladesh",
        "Sri Lanka",
    ]:
        assert marker in text
    assert "Total global corridors: `97`" in DOC.read_text(encoding="utf-8")


def test_global_corridor_runtime_distribution_is_documented() -> None:
    text = sdk()
    assert "scenarioCorridors.length" in text
    assert 'corridor("Australia", toCountry)' in text
    assert 'corridor("United States", toCountry)' in text
    assert 'corridor("Canada", toCountry)' in text
    assert 'corridor("United Kingdom", toCountry)' in text
    doc = DOC.read_text(encoding="utf-8")
    for row in [
        "| Australia | 17 |",
        "| United States | 17 |",
        "| Canada | 17 |",
        "| United Kingdom | 17 |",
        "| Europe | 10 |",
        "| Middle East | 9 |",
        "| Africa | 10 |",
    ]:
        assert row in doc


def test_global_corridor_registry_runtime_count_is_97() -> None:
    script = """
const ts = require('./novapay_consumer_app/node_modules/typescript');
const fs = require('fs');
const vm = require('vm');
let source = fs.readFileSync('packages/novatech-platform-sdk/src/index.ts', 'utf8');
source = source.replace(/^export \*.*$/gm, '');
source = source.replace(/export /g, '');
source += '\\nresult = { corridors: scenarioCorridors.length, documented: scenarioRegistrySummary.currentDocumentedJourneys, target: scenarioRegistrySummary.totalTarget, ids: scenarioCorridors.map((item) => item.corridorId) };';
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021 } }).outputText;
const sandbox = { result: null };
vm.createContext(sandbox);
vm.runInContext(js, sandbox);
console.log(JSON.stringify(sandbox.result));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, text=True, capture_output=True)
    assert '"corridors":97' in result.stdout
    assert '"documented":150' in result.stdout
    assert '"target":1120' in result.stdout
    for corridor_id in [
        "COR-AU-CD",
        "COR-AU-BI",
        "COR-AU-KE",
        "COR-US-CD",
        "COR-US-MX",
        "COR-US-PK",
        "COR-CA-CD",
        "COR-CA-BD",
        "COR-UK-CD",
        "COR-UK-LK",
        "COR-FR-CD",
        "COR-BE-RW",
        "COR-AE-IN",
        "COR-SA-BD",
        "COR-ZA-ZW",
        "COR-KE-UG",
        "COR-NG-GH",
    ]:
        assert corridor_id in result.stdout


def test_registry_classification_test_suite_and_evidence_enums_are_complete() -> None:
    text = sdk()
    for marker in [
        "Happy Path",
        "Alternative Path",
        "Exception",
        "Compliance",
        "Fraud",
        "Recovery",
        "Performance",
        "Security",
        "Accessibility",
        "Offline",
        "Integration",
        "Disaster Recovery",
        "Negative Testing",
        "Boundary Testing",
        "Production Certification",
        "Replay Evidence",
        "Audit Package",
        "Operator Log",
    ]:
        assert marker in text


def test_registry_domain_targets_sum_to_1120() -> None:
    text = sdk()
    targets = [int(value) for value in re.findall(r"target: (\d+),", text)]
    assert sum(targets) == 1120
    for domain in [
        "Consumer",
        "Business",
        "Merchant",
        "Wallet",
        "Agent Banking",
        "Government",
        "Compliance",
        "Fraud",
        "Customer Support",
        "Recovery",
        "API Integration",
        "Mobile UI",
        "Performance",
        "Accessibility",
    ]:
        assert f'domain: "{domain}"' in text


def test_registry_seed_contains_standard_metadata_examples() -> None:
    text = sdk()
    for marker in [
        "NP-CONS-001",
        "NP-FRAUD-001",
        "NP-API-001",
        'version: "2026.1"',
        'personaId: "PER-MIGRANT-WORKER"',
        'corridorId: "COR-AU-CD"',
        'currencies: "AUD -> CDF"',
        'amount: "AUD 500"',
        'receiveMethod: "Mobile Money"',
        'riskLevel: "Low"',
        'kycLevel: "Enhanced"',
        "amlRequired: true",
        "sanctionsCheck: true",
        "automation: true",
        "uiTest: true",
        "apiTest: true",
        "regression: true",
    ]:
        assert marker in text


def test_registry_document_exists_and_describes_architecture() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaTech Enterprise Scenario Registry 2026",
        "Standard Metadata",
        "Classifications",
        "Personas",
        "Corridor Library",
        "Test Coverage Matrix",
        "Evidence Requirements",
        "Total long-term target: `1120`",
        "NovaAI is advisory only",
    ]:
        assert marker in doc
