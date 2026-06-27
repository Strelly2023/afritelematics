from __future__ import annotations

import json
from pathlib import Path


def test_novapay_region_manifests_exist_and_are_distinct() -> None:
    base = Path("infra/aws/novatech-core-platform/environments")
    manifests = {
        "au": base / "au",
        "ke": base / "ke",
        "bi": base / "bi",
        "cd": base / "cd",
    }

    for region, manifest_dir in manifests.items():
        main_tf = manifest_dir / "main.tf"
        outputs_tf = manifest_dir / "outputs.tf"
        tfvars_json = manifest_dir / "terraform.tfvars.json"
        tfvars_example = manifest_dir / "terraform.tfvars.example"

        assert main_tf.exists(), region
        assert outputs_tf.exists(), region
        assert tfvars_json.exists(), region
        assert tfvars_example.exists(), region

        main_text = main_tf.read_text()
        assert 'source = "../.."' in main_text
        assert "novapay_secret_arns" in main_text
        assert "novapay_env_vars" in main_text

        outputs_text = outputs_tf.read_text()
        for output_name in (
            "rollout_mode",
            "primary_corridor",
            "corridors",
            "settlement_mode",
            "mobile_money_live_enabled",
            "compliance_provider",
            "compliance_live_enabled",
        ):
            assert f'output "{output_name}"' in outputs_text

        config = json.loads(tfvars_json.read_text())
        assert config["novapay_region"] == region.upper()
        assert config["novapay_primary_corridor"].startswith("AU->")
        assert isinstance(config["novapay_env_vars"], dict)
        assert isinstance(config["novapay_secret_arns"], dict)

    assert (manifests["au"] / "terraform.tfvars.json").read_text() != (
        manifests["ke"] / "terraform.tfvars.json"
    ).read_text()
    assert (manifests["bi"] / "terraform.tfvars.json").read_text() != (
        manifests["cd"] / "terraform.tfvars.json"
    ).read_text()
