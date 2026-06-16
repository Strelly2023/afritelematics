from __future__ import annotations

import json

from afritech.cli.main import main


def test_afritech_verify_registry_cli_json(capsys):
    assert main(["verify", "--registry", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["verified"] is True
    assert payload["signature_valid"] is True
    assert payload["signer_trusted"] is True
    assert payload["no_fake_feature_can_exist"] is True
    assert payload["no_incomplete_feature_can_appear"] is True
    assert payload["no_unverifiable_claim_can_be_exported"] is True
    assert payload["no_production_state_can_be_falsely_implied"] is True


def test_afritech_verify_global_cli_json(capsys):
    assert main(["verify", "--global", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["verified"] is True
    assert payload["classification"] == "LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER"
    assert payload["level"] == "LEVEL_15"
    assert payload["bundle_hash_valid"] is True
    assert payload["cross_network"]["network_count"] >= 3
    assert payload["guarantees"]["truth_independent_of_origin_system"] is True
    assert payload["guarantees"]["optional_onchain_anchoring_supported"] is True


def test_afritech_verify_ecosystem_cli_json(capsys):
    assert main(["verify", "--ecosystem", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["verified"] is True
    assert payload["classification"] == "LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE"
    assert payload["level"] == "LEVEL_16"
    assert payload["organizations"]["organization_count"] >= 3
    assert payload["government_adoption"]["government_profile_count"] >= 2
    assert payload["live_public_ledger_anchoring"]["verified"] is True
    assert payload["interoperable_standard"]["verified"] is True
    assert payload["guarantees"]["cross_government_adoption_ready"] is True
