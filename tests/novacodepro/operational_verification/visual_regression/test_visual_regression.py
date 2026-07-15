from afritech.novacodepro.operational_verification.visual_regression import VisualBaseline, verify_visual_regression


def test_approved_baseline_required() -> None:
    missing = verify_visual_regression(None, tool_ran=True, screens_checked=1)
    proposed = verify_visual_regression(VisualBaseline("base-1", "PROPOSED"), tool_ran=True, screens_checked=1)
    approved = verify_visual_regression(VisualBaseline("base-2", "APPROVED"), tool_ran=True, screens_checked=1)

    assert missing.verified is False
    assert proposed.verified is False
    assert approved.verified is True


def test_material_difference_blocks() -> None:
    result = verify_visual_regression(VisualBaseline("base", "APPROVED"), tool_ran=True, screens_checked=3, unapproved_differences=1)

    assert result.verified is False
