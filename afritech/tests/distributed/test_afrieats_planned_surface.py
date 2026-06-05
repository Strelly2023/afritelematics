from __future__ import annotations

from afritech.ci.afrieats_planned_surface_validator import DOC, ROOT, validate


def test_afrieats_planned_surface_validator_passes():
    assert validate() is True


def test_afrieats_keeps_structure_separate_from_reality():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "AfriEats Architecture: Conceptual" in text
    assert "AfriEats Field Evidence: None" in text
    assert "AfriEats Operational Truth: Not Yet Established" in text
    assert "Structure proven does not mean reality proven." in text


def test_afrieats_reality_capture_template_is_locked():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    for field in (
        "Order ID:",
        "Date + Time:",
        "Customer:",
        "Restaurant:",
        "Pickup:",
        "Dropoff:",
        "Driver:",
        "Items:",
        "Preparation Time:",
        "Pickup Time:",
        "Delivery Time:",
        "Outcome:",
        "Notes:",
    ):
        assert field in text
