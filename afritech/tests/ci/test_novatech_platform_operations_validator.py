from afritech.ci.novatech_platform_operations_validator import validate


def test_novatech_platform_operations_contract_passes() -> None:
    assert validate() is True
