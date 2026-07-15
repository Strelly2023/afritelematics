from afritech.novacodepro.operational_verification.digital_twin import TelemetryProfile, run_simulation, verify_telemetry_profile


def test_static_only_telemetry_does_not_verify() -> None:
    result = verify_telemetry_profile(TelemetryProfile(1000, True, True, True, True, True, True, static_seed_only=True))

    assert result["telemetry_connected"] is True
    assert result["verified"] is False


def test_insufficient_coverage_rejected() -> None:
    result = verify_telemetry_profile(TelemetryProfile(10, True, False, True, True, True, True))

    assert result["verified"] is False


def test_simulation_has_no_external_payment_side_effects() -> None:
    result = run_simulation("Payment-provider failure reference", seed=42)

    assert result.executed is True
    assert result.forbidden_side_effects is False
