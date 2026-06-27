from __future__ import annotations

from pathlib import Path


def test_novapay_region_manifests_exist_and_are_distinct() -> None:
    base = Path("infra/aws/novatech-core-platform/environments")
    manifests = {
        "au": base / "au/terraform.tfvars.example",
        "ke": base / "ke/terraform.tfvars.example",
        "bi": base / "bi/terraform.tfvars.example",
        "cd": base / "cd/terraform.tfvars.example",
    }

    for region, manifest in manifests.items():
        assert manifest.exists(), region
        text = manifest.read_text()
        assert f'novapay_region = "{region.upper()}"' in text
        assert "novapay_env_vars" in text
        assert "novapay_secret_arns" in text

    assert manifests["au"].read_text() != manifests["ke"].read_text()
    assert manifests["bi"].read_text() != manifests["cd"].read_text()
