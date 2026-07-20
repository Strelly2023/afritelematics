"""NovaTrust / NovaPay portal suite API surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novapay import NovaPayEcosystem
from afritech.novapay.portal_suite import NovaPortalSuite


def _suite() -> NovaPortalSuite:
    return NovaPortalSuite(NovaPayEcosystem.default())


def build_novaportal_suite_router(suite: NovaPortalSuite | None = None) -> APIRouter:
    portal = suite or _suite()
    router = APIRouter(tags=["novaportal-suite"])

    support = require_roles("OPERATOR", "ADMIN")
    compliance = require_roles("VERIFIER", "OBSERVER", "OPERATOR", "ADMIN")
    operations = require_roles("OPERATOR", "ADMIN")
    finance = require_roles("INVESTOR", "OPERATOR", "ADMIN")
    partners = require_roles("PARTNER", "OPERATOR", "ADMIN")
    inspector = require_roles("VERIFIER", "OBSERVER", "OPERATOR", "ADMIN")
    @router.get("/v1/novatrust/explorer")
    def novatrust_explorer() -> dict[str, Any]:
        return portal.trust_explorer()

    @router.get("/v1/novatrust/verify/receipt/{receipt_id}")
    def verify_receipt(receipt_id: str) -> dict[str, Any]:
        return portal.verify_receipt(receipt_id)

    @router.get("/v1/novatrust/verify/payment/{payment_id}")
    def verify_payment(payment_id: str) -> dict[str, Any]:
        return portal.verify_payment(payment_id)

    @router.get("/v1/novatrust/verify/ride/{ride_id}")
    def verify_ride(ride_id: str) -> dict[str, Any]:
        return portal.verify_ride(ride_id)

    @router.get("/v1/novatrust/replay/{identifier}")
    def replay(identifier: str) -> dict[str, Any]:
        return portal.replay(identifier)

    @router.get("/v1/novatrust/audit-bundles/{identifier}")
    def audit_bundle(identifier: str) -> dict[str, Any]:
        return portal.audit_bundle(identifier)

    @router.get("/v1/novapay/support/customers")
    def support_customers(claims: JWTClaims = Depends(support)) -> dict[str, Any]:
        return portal.support_customers()

    @router.get("/v1/novapay/support/cases")
    def support_cases(claims: JWTClaims = Depends(support)) -> dict[str, Any]:
        return portal.support_cases()

    @router.get("/v1/novapay/support/disputes")
    def support_disputes(claims: JWTClaims = Depends(support)) -> dict[str, Any]:
        return portal.support_disputes()

    @router.get("/v1/novapay/support/refunds")
    def support_refunds(claims: JWTClaims = Depends(support)) -> dict[str, Any]:
        return portal.support_refunds()

    @router.get("/v1/novapay/compliance/alerts")
    def compliance_alerts(claims: JWTClaims = Depends(compliance)) -> dict[str, Any]:
        return portal.compliance_alerts()

    @router.get("/v1/novapay/compliance/aml")
    def compliance_aml(claims: JWTClaims = Depends(compliance)) -> dict[str, Any]:
        return portal.compliance_aml()

    @router.get("/v1/novapay/compliance/sanctions")
    def compliance_sanctions(claims: JWTClaims = Depends(compliance)) -> dict[str, Any]:
        return portal.compliance_sanctions()

    @router.get("/v1/novapay/compliance/investigations")
    def compliance_investigations(claims: JWTClaims = Depends(compliance)) -> dict[str, Any]:
        return portal.compliance_investigations()

    @router.get("/v1/novapay/compliance/reports")
    def compliance_reports(claims: JWTClaims = Depends(compliance)) -> dict[str, Any]:
        return portal.compliance_reports()

    @router.get("/v1/novatech/operations/health")
    def operations_health(claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        return portal.operations_health()

    @router.get("/v1/novatech/operations/incidents")
    def operations_incidents(claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        return portal.operations_incidents()

    @router.get("/v1/novatech/operations/services")
    def operations_services(claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        return portal.operations_services()

    @router.get("/v1/novatech/operations/automation")
    def operations_automation(claims: JWTClaims = Depends(operations)) -> dict[str, Any]:
        return portal.operations_automation()

    @router.get("/v1/novapay/finance/ledger")
    def finance_ledger(claims: JWTClaims = Depends(finance)) -> dict[str, Any]:
        return portal.finance_ledger()

    @router.get("/v1/novapay/finance/settlements")
    def finance_settlements(claims: JWTClaims = Depends(finance)) -> dict[str, Any]:
        return portal.finance_settlements()

    @router.get("/v1/novapay/finance/reconciliation")
    def finance_reconciliation(claims: JWTClaims = Depends(finance)) -> dict[str, Any]:
        return portal.finance_reconciliation()

    @router.get("/v1/novapay/finance/reports")
    def finance_reports(claims: JWTClaims = Depends(finance)) -> dict[str, Any]:
        return portal.finance_reports()

    @router.get("/v1/novapay/partners")
    def partner_directory(claims: JWTClaims = Depends(partners)) -> dict[str, Any]:
        return portal.partner_directory()

    @router.get("/v1/novapay/partners/onboarding")
    def partner_onboarding(claims: JWTClaims = Depends(partners)) -> dict[str, Any]:
        return portal.partner_onboarding()

    @router.get("/v1/novapay/partners/certification")
    def partner_certification(claims: JWTClaims = Depends(partners)) -> dict[str, Any]:
        return portal.partner_certification()

    @router.get("/v1/novapay/partners/revenue")
    def partner_revenue(claims: JWTClaims = Depends(partners)) -> dict[str, Any]:
        return portal.partner_revenue()

    @router.get("/v1/novapay/partners/sla")
    def partner_sla(claims: JWTClaims = Depends(partners)) -> dict[str, Any]:
        return portal.partner_sla()

    @router.get("/v1/novapay/inspector/inspections")
    def inspector_inspections(claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        return portal.inspector_inspections()

    @router.get("/v1/novapay/inspector/evidence")
    def inspector_evidence(claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        return portal.inspector_evidence()

    @router.get("/v1/novapay/inspector/checklists")
    def inspector_checklists(claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        return portal.inspector_checklists()

    @router.get("/v1/novapay/inspector/incidents")
    def inspector_incidents(claims: JWTClaims = Depends(inspector)) -> dict[str, Any]:
        return portal.inspector_incidents()

    return router


__all__ = ["build_novaportal_suite_router"]
