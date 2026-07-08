"""Internal QA only mocked contract routes for pre-pilot validation."""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


def _ok(contract: str, action: str, **extra: object) -> dict[str, object]:
    return {"status": "ok", "contract": contract, "action": action, "mocked": True, **extra}


@router.post("/auth/register")
def auth_register() -> dict[str, object]:
    return _ok("internal_qa.auth.v1", "register")


@router.post("/auth/login")
def auth_login() -> dict[str, object]:
    return _ok("internal_qa.auth.v1", "login", token="qa-mock-token")


@router.post("/auth/logout")
def auth_logout() -> dict[str, object]:
    return _ok("internal_qa.auth.v1", "logout")


@router.post("/auth/otp/send")
def auth_otp_send() -> dict[str, object]:
    return _ok("internal_qa.auth.v1", "otp_send")


@router.post("/auth/otp/verify")
def auth_otp_verify() -> dict[str, object]:
    return _ok("internal_qa.auth.v1", "otp_verify")


@router.get("/novaid/profile")
def novaid_profile() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "profile")


@router.post("/novaid/verify/personal")
def novaid_verify_personal() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "verify_personal")


@router.post("/novaid/verify/business")
def novaid_verify_business() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "verify_business")


@router.post("/novaid/verify/employee")
def novaid_verify_employee() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "verify_employee")


@router.post("/novaid/verify/partner")
def novaid_verify_partner() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "verify_partner")


@router.post("/novaid/verify/inspector")
def novaid_verify_inspector() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "verify_inspector")


@router.post("/novaid/documents/upload")
def novaid_documents_upload() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "documents_upload")


@router.get("/novaid/activity")
def novaid_activity() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "activity")


@router.get("/novaid/audit")
def novaid_audit() -> dict[str, object]:
    return _ok("internal_qa.novaid.v1", "audit")


@router.get("/novapay/wallet")
def novapay_wallet() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "wallet", wallet_id="qa-wallet")


@router.get("/novapay/balance")
def novapay_balance() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "balance", balance_minor=0)


@router.post("/novapay/topup")
def novapay_topup() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "topup")


@router.post("/novapay/send")
def novapay_send() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "send")


@router.post("/novapay/receive")
def novapay_receive() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "receive")


@router.post("/novapay/cash-in")
def novapay_cash_in() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "cash_in")


@router.post("/novapay/cash-out")
def novapay_cash_out() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "cash_out")


@router.post("/novapay/qr/generate")
def novapay_qr_generate() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "qr_generate")


@router.post("/novapay/merchant/pay")
def novapay_merchant_pay() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "merchant_pay")


@router.post("/novapay/refunds")
def novapay_refunds() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "refunds")


@router.get("/novapay/settlements")
def novapay_settlements() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "settlements")


@router.post("/novapay/business/approvals")
def novapay_business_approvals() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "business_approvals")


@router.post("/novapay/business/payroll")
def novapay_business_payroll() -> dict[str, object]:
    return _ok("internal_qa.novapay.v1", "business_payroll")


@router.post("/rides/request")
def rides_request() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "request")


@router.post("/rides/accept")
def rides_accept() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "accept")


@router.post("/rides/start")
def rides_start() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "start")


@router.post("/rides/end")
def rides_end() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "end")


@router.post("/rides/cancel")
def rides_cancel() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "cancel")


@router.get("/rides/history")
def rides_history() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "history")


@router.get("/drivers/status")
def drivers_status() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "drivers_status")


@router.get("/operators/fleet")
def operators_fleet() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "operators_fleet")


@router.get("/operators/compliance")
def operators_compliance() -> dict[str, object]:
    return _ok("internal_qa.novaride.v1", "operators_compliance")


@router.post("/support/tickets")
def support_tickets() -> dict[str, object]:
    return _ok("internal_qa.support.v1", "tickets")


@router.post("/safety/sos")
def safety_sos() -> dict[str, object]:
    return _ok("internal_qa.safety.v1", "sos")


@router.get("/security/devices")
def security_devices() -> dict[str, object]:
    return _ok("internal_qa.security.v1", "devices")
