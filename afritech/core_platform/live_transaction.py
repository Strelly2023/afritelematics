"""Governed NovaPay live-transaction readiness and dry-run execution."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from afritech.core_platform.models import AuthorityDecision, Identity
from afritech.core_platform.payments.providers import mfs_africa_status
from afritech.core_platform.settlement import build_settlement_corridor_matrix, build_settlement_status
from afritech.core_platform.transfers import NovaPayTransferService


@dataclass(frozen=True)
class LiveTransactionScenario:
    sender_id: str
    organization_id: str
    recipient_name: str
    recipient_identifier: str
    recipient_country: str
    amount: Decimal
    source_currency: str = "AUD"
    payout_method: str = "mfs_africa"
    use_case: str = "fast_low_cost_international"
    memo: str = "NovaPay governed first transaction test"


def build_live_transaction_readiness() -> dict[str, Any]:
    provider = mfs_africa_status()
    settlement = build_settlement_status()
    corridors = build_settlement_corridor_matrix()
    ready_corridors = [
        row["corridor"]
        for row in corridors
        if row["execution_state"] == "live_ready"
    ]
    live_ready = bool(provider["ready_for_real_transaction"] and ready_corridors)
    return {
        "view": "novapay_live_transaction_readiness",
        "provider": provider,
        "settlement": settlement,
        "corridors": corridors,
        "ready_corridors": ready_corridors,
        "live_ready": live_ready,
        "default_mode": "dry_run",
        "required_live_controls": [
            "MFS_AFRICA_LIVE_MODE=true",
            "MFS_AFRICA_API_BASE_URL",
            "MFS_AFRICA_TOKEN_URL",
            "MFS_AFRICA_CLIENT_ID",
            "MFS_AFRICA_CLIENT_SECRET",
            "MFS_AFRICA_CALLBACK_URL",
            "MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE",
            "NOVAPAY_MOBILE_MONEY_LIVE_ENABLED=true",
            "NOVAPAY_COMPLIANCE_LIVE_ENABLED=true",
        ],
        "operator_confirmation_required": True,
        "real_money_movement_blocked": not live_ready,
    }


def run_first_transaction_test(
    scenario: LiveTransactionScenario,
    *,
    live: bool = False,
    operator_confirmed: bool = False,
) -> dict[str, Any]:
    readiness = build_live_transaction_readiness()
    transfers = NovaPayTransferService()
    identity = Identity(
        identity_id=scenario.sender_id,
        email=f"{scenario.sender_id}@novapay.local",
        roles=("OPERATOR",),
        scopes=("payments:write", "payments:read", "monitoring:read"),
        organization_id=scenario.organization_id,
    )
    quote = transfers.quote(
        identity=identity,
        recipient_name=scenario.recipient_name,
        recipient_identifier=scenario.recipient_identifier,
        recipient_country=scenario.recipient_country,
        amount=scenario.amount,
        source_currency=scenario.source_currency,
        payout_method=scenario.payout_method,
        use_case=scenario.use_case,
        memo=scenario.memo,
        live_provider=live,
    )
    quote_payload = quote.canonical()
    requested_corridor = str(quote_payload.get("corridor", "")).split(":", 1)[0]
    if live and (
        not operator_confirmed
        or not readiness["provider"]["ready_for_real_transaction"]
        or requested_corridor not in readiness["ready_corridors"]
    ):
        return {
            "view": "novapay_first_transaction_test",
            "status": "blocked",
            "mode": "live",
            "reason": "live_transaction_gate_not_satisfied",
            "readiness": readiness,
            "quote": quote_payload,
            "requested_corridor": requested_corridor,
        }
    decision = AuthorityDecision(
        decision="ALLOW",
        reason="operator_live_test_gate_passed",
        trace_id=f"novapay-live-test:{quote_payload['quote_id']}",
        checks=(
            "operator_role:present",
            "payments_write_scope:present",
            "identity_bound_to_jwt_claims",
            "live_provider_gate:passed" if live else "dry_run_gate:passed",
        ),
    )
    receipt = transfers.execute(
        quote,
        identity=identity,
        decision=decision,
        provider="mfs_africa",
        live_provider=live,
    )
    verification = transfers.verify(receipt.canonical())
    return {
        "view": "novapay_first_transaction_test",
        "status": "submitted" if live else "dry_run_complete",
        "mode": "live" if live else "dry_run",
        "live_network_called": live,
        "readiness": readiness,
        "quote": quote_payload,
        "decision": decision.canonical(),
        "receipt": receipt.canonical(),
        "verification": verification,
    }


__all__ = [
    "LiveTransactionScenario",
    "build_live_transaction_readiness",
    "run_first_transaction_test",
]
