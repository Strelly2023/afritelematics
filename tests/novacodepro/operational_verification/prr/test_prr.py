from afritech.novacodepro.operational_verification.prr import generate_prr_package, validate_prr_package


def test_package_derives_from_evidence_refs_and_blocks_ga() -> None:
    package = generate_prr_package("rel-1", ["ev-1"], "ci")
    validation = validate_prr_package(package)

    assert package.recommendation == "READY_FOR_PRR_APPROVAL"
    assert package.ga_allowed is False
    assert package.real_payments_enabled is False
    assert validation["valid"] is True


def test_development_signature_cannot_approve_production() -> None:
    package = generate_prr_package("rel-1", ["ev-1"], "production")
    validation = validate_prr_package(package, production=True)

    assert validation["valid"] is False
    assert validation["development_signature_blocks_production"] is True
