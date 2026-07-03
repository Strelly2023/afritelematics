from __future__ import annotations

from afritech.afripay.treasury_ai import TreasuryAI


def test_treasury_ai_flags_prefunding_gaps_and_produces_advisory_decisions() -> None:
    snapshot = {
        "liquidity_positions": [
            {
                "corridor_id": "au-ke",
                "currency": "AUD",
                "available_balance": "1000.00",
                "reserved_balance": "100.00",
            },
            {
                "corridor_id": "au-bi",
                "currency": "AUD",
                "available_balance": "250.00",
                "reserved_balance": "25.00",
            },
        ],
        "prefunding_accounts": [
            {
                "provider": "mtn_mobile_money",
                "currency": "AUD",
                "required_balance": "120.00",
                "current_balance": "80.00",
                "status": "warning",
            },
            {
                "provider": "bank_partner",
                "currency": "AUD",
                "required_balance": "200.00",
                "current_balance": "260.00",
                "status": "healthy",
            },
        ],
        "settlement_exposures": [
            {
                "provider": "mtn_mobile_money",
                "currency": "AUD",
                "amount_pending": "140.00",
                "status": "pending",
            }
        ],
    }

    intelligence = TreasuryAI().evaluate(snapshot)

    assert intelligence["classification"] == "NOVAPAY_TREASURY_AI_REPORT"
    assert intelligence["authority_boundary"] == "advisory_only_and_policy_gated"
    assert intelligence["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert intelligence["cash_balance"] == "1250.00"
    assert intelligence["reserved_balance"] == "125.00"
    assert intelligence["settlement_obligations"] == "140.00"
    assert intelligence["prefunding_gap"] == "40.00"
    assert intelligence["decision"]["action"] in {
        "increase_liquidity",
        "rebalance_treasury",
        "maintain_buffer",
        "invest_growth",
    }
    assert intelligence["recommendations"]
    assert intelligence["stress_tests"]
    assert intelligence["provider_snapshot"][0]["provider"] == "mtn_mobile_money"
    assert intelligence["provider_snapshot"][0]["prefunding_gap"] == "40.00"
