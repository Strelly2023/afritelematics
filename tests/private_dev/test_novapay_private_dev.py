from __future__ import annotations

import pytest

from tests.private_dev._helpers import assert_contains_all, read_json, read_text


pytestmark = [pytest.mark.private_dev, pytest.mark.novapay]


def test_novapay_consumer_agent_merchant_business_surfaces_exist() -> None:
    registry = read_json("docs/mobile/private_dev_button_registry.json")["apps"]

    for app_key in (
        "novapay_consumer",
        "novapay_agent",
        "novapay_merchant",
        "novapay_business",
    ):
        spec = registry[app_key]
        source = read_text(spec["source"])
        assert_contains_all(source, list(spec["tabs"]), context=f"{app_key} tabs")
        assert_contains_all(source, list(spec["buttons"]), context=f"{app_key} buttons")
        assert "TODO" not in source
        assert "console.log(" not in source


def test_novapay_private_dev_flows_do_not_require_novaride() -> None:
    consumer_source = read_text("novapay_consumer_app/src/roleApp.tsx")
    agent_source = read_text("novapay_agent_app/src/agentApp.tsx")
    merchant_source = read_text("novapay_merchant_app/src/roleApp.tsx")
    business_source = read_text("novapay_business_app/src/roleApp.tsx")

    for source in (consumer_source, agent_source, merchant_source, business_source):
        assert "stripe_live" not in source
        assert "flutterwave_live" not in source
