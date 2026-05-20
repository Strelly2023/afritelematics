from __future__ import annotations

import re
from pathlib import Path


DOC = Path(__file__).resolve().parents[3] / "docs/qa/AfriRide_Test_Cases.md"

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL VALIDATION SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL VALIDATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale marketplace guarantees achieved",
)

SECTIONS = (
    "Ride Request Test Cases",
    "Driver Matching Test Cases",
    "Ride Lifecycle Test Cases",
    "Full Ride Flow Test Cases",
    "Cancellation Test Cases",
    "Pricing Test Cases",
    "Notification Test Cases",
    "Payment Test Cases",
    "Replay and Audit Test Cases",
    "Continuity Test Cases",
    "Governance Test Cases",
    "API Test Cases",
)

COMPONENTS = (
    "RideRequestService",
    "RideRequestValidator",
    "MatchingService",
    "RideLifecycleService",
    "PricingService",
    "NotificationService",
    "PaymentService",
    "RideEvent / Audit",
    "Replay/Audit",
    "Claim discipline validator",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_test_cases_have_operational_validation_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "under afritech constitutional admissibility constraints" in lowered
    assert "they do not prove" in lowered
    assert "global deployment readiness" in lowered
    assert "universal fault tolerance" in lowered
    assert "complete state-space exhaustiveness" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_test_cases_are_numbered_contiguously() -> None:
    text = read_doc()
    case_ids = re.findall(r"## (TC-\d{3}) - ", text)

    assert case_ids == [f"TC-{number:03d}" for number in range(1, 39)]
    assert len(set(case_ids)) == 38


def test_test_cases_cover_required_validation_sections() -> None:
    text = read_doc()

    for section in SECTIONS:
        assert section in text

    for component in COMPONENTS:
        assert component in text


def test_test_cases_cover_request_matching_and_lifecycle_behavior() -> None:
    text = read_doc()

    for expected in (
        "Ride is created with `REQUESTED` status",
        "`ValueError(\"Missing field: origin\")`",
        "`ValueError(\"Missing field: destination\")`",
        "Same driver selected",
        "Ride status becomes `MATCHED`",
        "Ride status becomes `ACCEPTED`",
        "Ride status becomes `STARTED`",
        "Ride status becomes `COMPLETED`",
        "Invalid transition rejected",
        "`REQUESTED -> MATCHED -> ACCEPTED -> STARTED -> COMPLETED`",
    ):
        assert expected in text


def test_test_cases_cover_cancellation_pricing_notifications_and_payments() -> None:
    text = read_doc()

    for expected in (
        "Ride status becomes `CANCELLED`",
        "Fare estimate returned",
        "Same fare returned",
        "Notification created/sent",
        "Ride status remains authoritative",
        "Payment enters `AUTHORIZED` or `PAID` state",
        "Payment failure recorded; ride lineage remains intact",
    ):
        assert expected in text


def test_test_cases_cover_replay_continuity_and_governance() -> None:
    text = read_doc()

    for expected in (
        "Replay-safe event stored",
        "Reconstructed status equals final ride status",
        "Replay invalid",
        "Recovery occurs deterministically",
        "Timeout handled without duplicate authority",
        "Same reassignment result under replay",
        "Only one authority accepted",
        "Every implemented claim has evidence binding",
        "`implementation_refs` exist in registry",
        "Claim references `PLANNED` surface",
        "Docs cannot redefine proof truth",
    ):
        assert expected in text


def test_test_cases_cover_api_behavior() -> None:
    text = read_doc()

    for expected in (
        "`POST /api/v1/rides`",
        "`POST /api/v1/rides/{ride_id}/transition`",
        "`201 Created`, status `REQUESTED`",
        "`400 Bad Request`",
        "`REQUESTED -> COMPLETED`",
    ):
        assert expected in text


def test_test_cases_define_acceptance_and_safe_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for criterion in (
        "all critical tests pass",
        "full ride flow passes",
        "replay validation passes",
        "continuity scenarios pass",
        "claim-evidence-implementation validation passes",
        "documentation boundary tests pass",
    ):
        assert criterion in lowered

    assert "bounded product behavior" in lowered
    assert "deterministic lifecycle execution" in lowered
    assert "replay-safe auditability" in lowered
    assert "constitutional admissibility constraints" in lowered
