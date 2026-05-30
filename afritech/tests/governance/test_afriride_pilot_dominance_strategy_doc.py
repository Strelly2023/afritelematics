from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Pilot_Dominance_Strategy.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_pilot_dominance_strategy_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "STATUS: BOUNDED PRODUCT DOMINANCE STRATEGY" in text
    assert "CLASSIFICATION: AFRIRIDE ONE-CITY MARKET PROOF SURFACE" in text
    assert "not runtime authority" in lowered
    assert "not evidence that a real city pilot has already succeeded" in lowered
    assert "launching everything" in lowered
    assert "prove everything" in lowered


def test_pilot_dominance_strategy_declares_single_battlefield() -> None:
    text = read_doc()

    assert "AfriRide" in text
    assert "build the best ride system in one city" in text
    assert "The mission is not \"launch the AfriTech ecosystem.\"" in text

    for reason in (
        "transport is daily",
        "valuable",
        "visible",
        "dispute-prone",
        "deterministic pricing",
        "replay proof",
    ):
        assert reason in text


def test_pilot_dominance_strategy_translates_internal_pillars() -> None:
    text = read_doc()

    for translation in (
        "Deterministic execution -> No random pricing",
        "Replay legitimacy -> Every trip can be proven",
        "Data locality -> Faster matching",
        "Observability -> Full transparency",
        "Governance -> No manipulation",
    ):
        assert translation in text

    assert "AfriRide is the only ride system where every trip is provable, fair, and cannot be manipulated." in text


def test_pilot_dominance_strategy_defines_pilot_gates() -> None:
    text = read_doc()

    for scale in ("city_count: 1", "drivers: 10-50", "users: 100-300"):
        assert scale in text

    for metric in (
        "replay consistency",
        "zero pricing anomalies",
        "dispatch determinism",
        "booking time",
        "ride success rate",
        "disputes",
        "refund cases",
        "driver complaints",
    ):
        assert metric in text

    for response in ("show replay", "explain exactly why", "prove system fairness"):
        assert response in text


def test_pilot_dominance_strategy_defines_loops_and_uber_positioning() -> None:
    text = read_doc()

    for loop in ("Trust Loop", "Driver Loyalty Loop", "Governance Advantage Loop"):
        assert loop in text

    for comparison in (
        "Uber: black box",
        "AfriRide: transparent",
        "Uber: surge randomness",
        "AfriRide: deterministic pricing",
        "Uber guesses. We prove.",
    ):
        assert comparison in text


def test_pilot_dominance_strategy_hides_internal_complexity() -> None:
    text = read_doc()
    before_boundary = text.split("External language must not lead with:", maxsplit=1)[0]

    for phrase in (
        "GA Elite",
        "18 pillars",
        "constitutional layers",
        "complete ecosystem",
        "autonomous civilization platform",
    ):
        assert phrase in text
        assert phrase not in before_boundary

    for external_value in (
        "rides",
        "fairness",
        "reliability",
        "proof when something goes wrong",
    ):
        assert external_value in text


def test_pilot_dominance_strategy_declares_stage_roadmap() -> None:
    text = read_doc()

    for stage in (
        "Stage 1: 0-3 Months",
        "launch one city pilot",
        "onboard 50 drivers",
        "Stage 2: 3-6 Months",
        "validate pricing correctness",
        "Stage 3: 6-12 Months",
        "expand to 2-3 cities only after pilot gates pass",
        "Stage 4: 12+ Months",
        "introduce logistics",
        "introduce delivery",
        "introduce payments",
    ):
        assert stage in text
