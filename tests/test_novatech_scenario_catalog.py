from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "packages/novatech-platform-sdk/src/index.ts"
DOC = ROOT / "docs/architecture/NOVATECH_SCENARIO_CATALOG_2026.md"


def source() -> str:
    return SDK.read_text(encoding="utf-8")


def test_scenario_catalog_covers_scenarios_2_to_20() -> None:
    text = source()
    scenario_ids = sorted(int(value) for value in re.findall(r"\n\s+id: (\d+),", text))
    assert scenario_ids == list(range(2, 21))
    assert "export const novaTechScenarioCatalog" in text
    assert "readonly NovaTechScenario[]" in text


def test_scenario_catalog_contains_required_customer_references() -> None:
    text = source()
    for marker in [
        "Sarah Johnson",
        "Jean-Pierre Mukendi",
        "Melbourne Fresh Foods Pty Ltd",
        "Congo Coffee Export SARL",
        "Mama Chantal Ilunga",
        "University of Lubumbashi",
        "Dr. Denis Hospital Billing Office",
        "Rukia Kazibulaya",
        "Grace Mwamba",
        "Patrick Mwamba",
        "Jean Claude Mbuyi",
        "Maria Gonzalez",
        "Congo African Grocery",
        "David Wilson",
        "Amina Kasongo",
        "Grace African Boutique",
        "David Mukeba",
        "Emma Thompson",
        "Emmanuel Kabila",
        "Sarah Mwangi",
        "Chantal Fashion Boutique",
        "Bahati Kasereka",
        "Amani Kasereka",
    ]:
        assert marker in text


def test_scenario_catalog_contains_required_references_and_channels() -> None:
    text = source()
    for marker in [
        "NP-2026-00073215",
        "NPB-2026-004812",
        "NP-2026-009843",
        "NPE-2026-001284",
        "NPM-2026-004251",
        "NP-2026-012548",
        "NP-2026-014682",
        "NPB-2026-021584",
        "NR-2026-000984",
        "NP-2026-015482",
        "NRP-2026-003984",
        "NT-2026-ONBOARD-013",
        "NRD-2026-000815",
        "NP-2026-021482",
        "NR-2026-VISA-016",
        "MIT-2026-4587",
        "NPA-2026-008412",
        "NPB-2026-030841",
        "NMC-2026-002419",
        "Bank Deposit",
        "Cash Pickup",
        "Mobile Money",
        "NovaPay QR",
        "Existing Visa Card via NovaPay Gateway",
        "Medical Transport and Healthcare Payment",
    ]:
        assert marker in text


def test_scenario_catalog_preserves_independent_product_boundaries() -> None:
    text = source()
    assert "NovaPay executes a bank-deposit remittance without NovaRide" in text
    assert "NovaPay Wallet is optional" in text
    assert "NovaPay can act as a gateway for external cards" in text
    assert "NovaRide owns transport; NovaPay owns hospital payment" in text
    assert "The customer chooses NovaID only, NovaPay, NovaRide, or all three" in text
    assert "NovaAI may recommend routes only" in text
    assert "advisory only" in text


def test_scenario_catalog_document_exists_and_matches_sdk_scope() -> None:
    doc = DOC.read_text(encoding="utf-8")
    assert "NovaTech Scenario Catalog 2026" in doc
    assert "Scenario Matrix" in doc
    assert "Scenario 16 uses NovaRide with an existing Visa card" in doc
    assert "NovaAI is advisory only" in doc
    for scenario_id in range(2, 21):
        assert f"| {scenario_id} |" in doc


def test_novapay_consumer_payment_catalog_covers_scenarios_20_to_99() -> None:
    text = source()
    ids = sorted(int(value) for value in re.findall(r"consumerScenario\((\d+),", text))
    assert ids == list(range(20, 100))
    assert "export const novapayConsumerScenarioCatalog" in text
    assert "readonly NovaPayConsumerPaymentScenario[]" in text


def test_novapay_consumer_payment_catalog_has_required_corridors_and_methods() -> None:
    text = source()
    for marker in [
        "First Salary Sent Home",
        "Monthly Rent Payment",
        "School Fees for Child",
        "Emergency Funeral Support",
        "Wedding Contribution",
        "Medical Insurance Payment",
        "Utility Bill Payment",
        "Mobile Airtime Purchase",
        "Disaster Relief Donation",
        "Visa Application Fee",
        "Import Goods Payment",
        "Wholesale Purchase",
        "Hotel Reservation Abroad",
        "Digital Freelancer Payment",
        "Remote Software Developer Payment",
        "Contractor Final Payment",
        "Salary to Family",
        "Emergency Medical Support",
        "University Tuition",
        "Family Monthly Support",
        "Passport Fee Payment",
        "Hotel Deposit",
        "Salary Remittance",
        "House Construction Payment",
        "Business Supplier Settlement",
        "Mobile Money",
        "Bank Deposit",
        "Institution Payment",
        "Cash Pickup",
        "Bill Pay",
        "Airtime",
        "Card/Wallet",
        "Burundi",
        "Democratic Republic of Congo",
    ]:
        assert marker in text


def test_novapay_consumer_feature_catalog_has_51_lifecycle_journeys() -> None:
    text = source()
    feature_ids = re.findall(r'consumerFeature\("NPF-(\d+)"', text)
    assert len(feature_ids) == 51
    assert feature_ids[0] == "001"
    assert feature_ids[-1] == "051"
    for marker in [
        "New user registration",
        "Identity verification with NovaID",
        "Wallet creation",
        "Schedule recurring transfers",
        "Transfer cancellation before processing",
        "Chargeback dispute",
        "Transaction replay",
        "Download PDF receipt",
        "Multi-currency wallet",
        "Scan-to-pay",
        "Agent-assisted cash withdrawal",
        "Transaction history search",
        "Budget insights",
        "Lost phone recovery",
        "Fraud alert handling",
        "Compliance document resubmission",
        "Tax statement generation",
        "Language switching",
        "Accessibility mode",
    ]:
        assert marker in text


def test_novapay_consumer_catalog_pushes_total_journeys_above_100() -> None:
    text = source()
    cross_product = len(re.findall(r"\n\s+id: \d+,", text))
    consumer_payments = len(re.findall(r"consumerScenario\(\d+,", text))
    consumer_features = len(re.findall(r'consumerFeature\("NPF-\d+"', text))
    assert cross_product + consumer_payments + consumer_features >= 150


def test_novapay_consumer_catalog_preserves_independence_from_novaride() -> None:
    text = source()
    assert 'novaRideRequired: false' in text
    assert 'novaPayOwns: "payment_execution"' in text
    assert "NovaRide is not required for NovaPay Consumer scenarios" in DOC.read_text(encoding="utf-8")
