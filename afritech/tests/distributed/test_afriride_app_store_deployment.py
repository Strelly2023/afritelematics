from __future__ import annotations

from pathlib import Path

from afritech.ci.afriride_app_store_deployment_validator import validate


def test_afriride_app_store_deployment_validator_passes():
    assert validate() is True


def test_app_store_docs_include_pilot_claim_discipline():
    master_plan = Path("docs/mobile/afriride_app_store_master_plan.md").read_text(
        encoding="utf-8"
    )
    listing = Path("docs/mobile/store_listing_content.md").read_text(
        encoding="utf-8"
    )

    assert "controlled pilot release" in master_plan
    assert "Live public production claims may not" in master_plan
    assert "Do Not Claim" in listing


def test_mobile_api_contract_includes_protocol_endpoints():
    contract = Path("docs/api/afriride_mobile_api_contract.md").read_text(
        encoding="utf-8"
    )

    assert "GET /ledger/:ride_id" in contract
    assert "GET /state/ride/:id" in contract
    assert "GET /trust/node/:id" in contract
    assert "Mobile apps are interface-only" in contract
