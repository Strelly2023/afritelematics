"""NovaRide/NovaPay financial boundary guard."""


def assert_novaride_payment_reference_only(operation: str) -> None:
    if operation in {"ledger_write", "settlement_execute", "refund_execute", "payout_execute", "loan_approve", "insurance_bind"}:
        raise PermissionError(f"novapay_authority_required:{operation}")
