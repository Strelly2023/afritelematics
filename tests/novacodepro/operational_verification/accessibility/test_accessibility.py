from afritech.novacodepro.operational_verification.accessibility import AccessibilityRunConfig, verify_accessibility


def test_axe_critical_violation_blocks() -> None:
    result = verify_accessibility(AccessibilityRunConfig(("/",)), tools_ran=True, critical=1)

    assert result.verified is False
    assert result.critical_violations == 1


def test_keyboard_failure_blocks_and_screen_reader_stays_separate() -> None:
    result = verify_accessibility(AccessibilityRunConfig(("/",)), tools_ran=True, keyboard=False)

    assert result.verified is False
    assert result.keyboard_navigation == "FAIL"
    assert result.screen_reader_automated_baseline == "PASS"
    assert result.screen_reader_human_validation == "PENDING"
