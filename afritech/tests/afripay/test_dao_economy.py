from __future__ import annotations

from afritech.afripay.dao_economy import DAOEconomyAI


def test_dao_economy_ai_builds_token_governance_and_allocation_plan() -> None:
    snapshot = {
        "accounts": [],
        "journals": [],
        "outbox": [{"status": "published"} for _ in range(6)],
        "snapshots": [{"version": 1}, {"version": 2}],
        "liquidity_positions": [
            {
                "corridor_id": "au-ke",
                "currency": "AUD",
                "available_balance": "150000.00",
                "reserved_balance": "5000.00",
            },
            {
                "corridor_id": "ke-bi",
                "currency": "KES",
                "available_balance": "90000.00",
                "reserved_balance": "3000.00",
            },
            {
                "corridor_id": "us-global",
                "currency": "USD",
                "available_balance": "60000.00",
                "reserved_balance": "2000.00",
            },
        ],
        "prefunding_accounts": [
            {
                "provider": "bank_partner",
                "currency": "USD",
                "required_balance": "50000.00",
                "current_balance": "42000.00",
                "status": "warning",
            }
        ],
        "settlement_exposures": [
            {
                "transfer_id": "tx-1",
                "currency": "KES",
                "amount_pending": "24000.00",
                "status": "pending",
            }
        ],
    }

    intelligence = DAOEconomyAI().evaluate(snapshot)

    assert intelligence["classification"] == "NOVARIDE_DAO_TOKEN_ECONOMY_REPORT"
    assert intelligence["authority_boundary"] == "advisory_only_and_policy_gated"
    assert intelligence["token_economy"]["symbol"] == "NVT"
    assert intelligence["token_economy"]["total_supply"] == "10000000.00"
    assert intelligence["token_economy"]["circulating_supply"] == "6000000.00"
    assert intelligence["governance"]["active_proposals"] == 5
    assert intelligence["governance"]["voting_model"] == "token_weighted_proposal_governance"
    assert intelligence["governance"]["proposal_queue"]
    assert intelligence["treasury"]["allocation_plan"]
    assert intelligence["onchain"]["proposal_batch_plan"]
    assert intelligence["onchain"]["treasury_batch_plan"]
    assert intelligence["metrics"]["token_supply"] == "10000000.00"
    assert intelligence["recommendations"]
