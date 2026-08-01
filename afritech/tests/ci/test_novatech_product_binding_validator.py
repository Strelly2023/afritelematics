from pathlib import Path

import pytest
import yaml

from afritech.ci.novatech_product_binding_validator import (
    ROOT,
    ProductBindingViolation,
    validate_novaid_binding,
)


def test_novaid_product_binding_resolves() -> None:
    assert validate_novaid_binding() is True


def test_novaid_product_binding_fails_closed_when_authority_is_incomplete(
    tmp_path: Path,
) -> None:
    source = ROOT / "afritech/governance/bindings/BIND-NOVAID-PRODUCT.yaml"
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    payload["authority"]["capabilities"].remove("authentication")
    candidate = tmp_path / "binding.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ProductBindingViolation, match="capabilities are incomplete"):
        validate_novaid_binding(candidate)
