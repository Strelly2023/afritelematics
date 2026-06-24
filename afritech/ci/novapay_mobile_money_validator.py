"""Validate the governed NovaPay multi-country mobile-money surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "afritech/governance/adr/ADR-0048-novapay-multi-country-mobile-money.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-068-novapay-multi-country-mobile-money.yaml"
BIND = ROOT / "afritech/governance/bindings/BIND-046-novapay-multi-country-mobile-money.yaml"
PROVIDER = ROOT / "afritech/core_platform/payments/mobile_money.py"
API = ROOT / "afritech/api/core_platform_api.py"
TEST = ROOT / "afritech/tests/core_platform/test_mobile_money.py"
DOC = ROOT / "docs/architecture/NOVAPAY_MULTI_COUNTRY_MOBILE_MONEY.md"
ENV = ROOT / "deploy/production/.env.production.trust-node.example"

VALIDATOR_NAME = "afritech.ci.novapay_mobile_money_validator"


@dataclass(frozen=True)
class MobileMoneyValidatorReport:
    governance_chain: bool
    countries_present: bool
    providers_present: bool
    pending_boundary: bool
    callback_security: bool
    trust_receipt: bool
    production_configuration: bool
    tests_present: bool

    @property
    def verified(self) -> bool:
        return all(
            (
                self.governance_chain,
                self.countries_present,
                self.providers_present,
                self.pending_boundary,
                self.callback_security,
                self.trust_receipt,
                self.production_configuration,
                self.tests_present,
            )
        )


def validate() -> MobileMoneyValidatorReport:
    adr = ADR.read_text(encoding="utf-8") if ADR.exists() else ""
    rule = RULE.read_text(encoding="utf-8") if RULE.exists() else ""
    binding = BIND.read_text(encoding="utf-8") if BIND.exists() else ""
    provider = PROVIDER.read_text(encoding="utf-8") if PROVIDER.exists() else ""
    api = API.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8") if TEST.exists() else ""
    docs = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    environment = ENV.read_text(encoding="utf-8")

    governance_chain = all(
        (
            "ADR-0048" in adr,
            "RULE-068" in rule,
            "BIND-046" in binding,
            "IA-NPMM-006" in adr,
        )
    )
    countries_present = all(marker in provider for marker in ('"BI"', '"CD"', '"KE"'))
    providers_present = all(
        marker in provider
        for marker in (
            "mpesa_ke",
            "airtel_money_ke",
            "lumicash_bi",
            "ecocash_bi",
            "orange_money_cd",
            "airtel_money_cd",
            "mpesa_cd",
        )
    )
    pending_boundary = all(
        marker in provider
        for marker in (
            'status="pending"',
            'settlement_status="pending_user_authorization"',
            "commercial_approval_reference",
            "NOVAPAY_MOBILE_MONEY_LIVE_ENABLED",
        )
    ) and "Provider initiation never means settlement" in docs
    callback_security = all(
        marker in api
        for marker in (
            "verify_webhook",
            "save_settlement_event",
            "find_payment",
            "provider_callback_authenticated",
        )
    )
    trust_receipt = all(
        marker in api
        for marker in (
            "core.payment.",
            "save_trust_receipt",
            "settlement_trust",
            "trust_explorer",
        )
    )
    production_configuration = all(
        marker in environment
        for marker in (
            "NOVAPAY_MOBILE_MONEY_LIVE_ENABLED=false",
            "NOVAPAY_MPESA_KE_CONSUMER_KEY=",
            "NOVAPAY_LUMICASH_BI_COLLECTION_URL=",
            "NOVAPAY_ORANGE_CD_COLLECTION_URL=",
        )
    )
    tests_present = all(
        marker in tests
        for marker in (
            "test_mobile_money_catalog_covers_burundi_kenya_and_drc",
            "test_mpesa_live_adapter_builds_daraja_stk_push",
            "test_mobile_money_api_and_settlement_create_separate_trust_receipt",
        )
    )
    return MobileMoneyValidatorReport(
        governance_chain=governance_chain,
        countries_present=countries_present,
        providers_present=providers_present,
        pending_boundary=pending_boundary,
        callback_security=callback_security,
        trust_receipt=trust_receipt,
        production_configuration=production_configuration,
        tests_present=tests_present,
    )


def main() -> int:
    report = validate()
    status = "PASSED" if report.verified else "FAILED"
    print(
        f"{VALIDATOR_NAME} {status} | governance={report.governance_chain} "
        f"countries={report.countries_present} providers={report.providers_present} "
        f"pending={report.pending_boundary} callbacks={report.callback_security} "
        f"trust={report.trust_receipt} config={report.production_configuration} "
        f"tests={report.tests_present}"
    )
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
