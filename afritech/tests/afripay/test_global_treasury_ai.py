from __future__ import annotations

from afritech.afripay.global_treasury_ai import GlobalTreasuryAI


def test_global_treasury_ai_builds_currency_distribution_and_onchain_plan() -> None:
    snapshot = {
        "ledger_checkpoint": {"snapshot_hash": "a" * 64},
        "global_ledger_root": "b" * 64,
        "liquidity_positions": [
            {
                "corridor_id": "au-ke",
                "currency": "AUD",
                "available_balance": "1000.00",
                "reserved_balance": "100.00",
            },
            {
                "corridor_id": "ke-bi",
                "currency": "KES",
                "available_balance": "600.00",
                "reserved_balance": "50.00",
            },
            {
                "corridor_id": "us-global",
                "currency": "USD",
                "available_balance": "400.00",
                "reserved_balance": "25.00",
            },
        ],
        "prefunding_accounts": [
            {
                "provider": "bank_partner",
                "currency": "USD",
                "required_balance": "500.00",
                "current_balance": "420.00",
                "status": "warning",
            }
        ],
        "settlement_exposures": [
            {
                "transfer_id": "tx-1",
                "currency": "KES",
                "amount_pending": "140.00",
                "status": "pending",
            }
        ],
    }

    intelligence = GlobalTreasuryAI().evaluate(snapshot)

    assert intelligence["classification"] == "NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_REPORT"
    assert intelligence["authority_boundary"] == "advisory_only_and_policy_gated"
    assert intelligence["core"]["classification"] == "NOVAPAY_TREASURY_AI_REPORT"
    assert intelligence["multi_currency"]["base_currency"] == "USD"
    assert intelligence["multi_currency"]["currency_totals"]["AUD"] == "1000.00"
    assert intelligence["multi_currency"]["currency_totals"]["KES"] == "600.00"
    assert intelligence["multi_currency"]["currency_totals"]["USD"] == "400.00"
    assert intelligence["multi_currency"]["currency_distribution"]
    assert intelligence["multi_currency"]["fx_exposure"]
    assert intelligence["multi_currency"]["stablecoin_ratio"]
    assert intelligence["multi_currency"]["stablecoin_target"]["strategy"] == "reserve_to_stablecoin"
    assert intelligence["multi_currency"]["hedge_actions"]
    assert intelligence["onchain"]["batch_strategy"] == "anchorBatchV2"
    assert intelligence["onchain"]["anchor_batch_plan"]
    assert intelligence["onchain"]["batch_size"] == len(intelligence["onchain"]["anchor_batch_plan"])
    assert intelligence["metrics"]["currency_count"] == 3
    assert intelligence["metrics"]["anchor_count"] >= 1
    assert intelligence["recommendations"]
