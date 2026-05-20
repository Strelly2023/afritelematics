from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/architecture/AfriRide_Software_Design_Document.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL DESIGN SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL DESIGN SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay admissibility",
    "core invariants",
    "execution legality",
    "identity ontology",
    "proof authority",
)

PACKAGE_PATHS = (
    "afriride_system/",
    "django_app/",
    "api/",
    "v1/",
    "ride_request_service.py",
    "input_validator.py",
    "matching_service.py",
    "lifecycle_service.py",
    "pricing_service.py",
    "payment_service.py",
    "notification_service.py",
)

COMPONENTS = (
    "Ride Request Service",
    "Ride Request Validator",
    "Matching Service",
    "Ride Lifecycle Service",
    "Pricing Service",
    "Notification Service",
    "Payment Service",
)

VALID_TRANSITIONS = (
    "REQUESTED -> MATCHED",
    "MATCHED -> ACCEPTED",
    "ACCEPTED -> STARTED",
    "STARTED -> COMPLETED",
    "REQUESTED -> CANCELLED",
    "MATCHED -> CANCELLED",
    "ACCEPTED -> CANCELLED",
)

FORBIDDEN_TRANSITIONS = (
    "REQUESTED -> COMPLETED",
    "MATCHED -> STARTED",
    "COMPLETED -> CANCELLED",
    "CANCELLED -> STARTED",
)

TRACEABILITY_ROWS = (
    "| Ride request | RideRequestService |",
    "| Input validation | RideRequestValidator |",
    "| Driver matching | MatchingService |",
    "| Lifecycle transitions | RideLifecycleService |",
    "| Pricing | PricingService |",
    "| Notifications | NotificationService |",
    "| Payments | PaymentService |",
    "| Replay audit | Replay/Audit event design |",
    "| Continuity | Continuity tests |",
    "| Constitutional boundary | Governance tests |",
)

FORBIDDEN_INFLATION = (
    "global marketplace scaling guarantees achieved",
    "complete distributed consensus achieved",
    "unbounded dispatch optimization achieved",
    "production payment settlement guarantees achieved",
    "formal completeness proof achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_sdd_has_operational_design_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_sdd_declares_design_scope_and_exclusions() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "django application structure" in lowered
    assert "ride request service design" in lowered
    assert "replay/audit alignment" in lowered
    assert "global marketplace scaling guarantees" in lowered
    assert "complete distributed consensus" in lowered
    assert "unbounded dispatch optimization" in lowered
    assert "production payment settlement guarantees" in lowered
    assert "formal completeness proof" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_sdd_defines_high_level_flow_and_package_structure() -> None:
    text = read_doc()

    assert "Client / API" in text
    assert "Django API layer" in text
    assert "AfriTech constitutional validation" in text
    assert "AfriRide may execute operational mobility behavior" in text
    assert "but may not redefine AfriTech truth" in text

    for path in PACKAGE_PATHS:
        assert path in text


def test_sdd_defines_component_design_contracts() -> None:
    text = read_doc()

    for component in COMPONENTS:
        assert component in text

    assert "validate input before creation" in text
    assert "do not perform driver matching here" in text
    assert 'raise ValueError("Missing field: <field>")' in text
    assert "matching must be deterministic" in text
    assert 'raise ValueError("Invalid transition")' in text
    assert "notification delivery failure must not mutate ride truth" in text
    assert "must not corrupt replay lineage" in text


def test_sdd_preserves_data_api_and_state_design() -> None:
    text = read_doc()

    for model in ("class Ride:", "class Driver:", "class Rider:"):
        assert model in text

    for endpoint in (
        "POST /api/v1/rides",
        "GET /api/v1/rides/{ride_id}",
        "POST /api/v1/rides/{ride_id}/transition",
    ):
        assert endpoint in text

    for transition in VALID_TRANSITIONS:
        assert transition in text

    for transition in FORBIDDEN_TRANSITIONS:
        assert transition in text


def test_sdd_defines_error_replay_and_test_design() -> None:
    text = read_doc()

    for error in (
        "missing rider_id",
        "invalid transition",
        "no eligible driver",
        "authorization failed",
        "delivery failed",
    ):
        assert error in text

    for event in (
        "ride_created",
        "driver_matched",
        "ride_accepted",
        "ride_started",
        "ride_completed",
        "ride_cancelled",
    ):
        assert event in text

    for test_case in (
        "RideRequestValidator rejects missing fields",
        "RideLifecycleService rejects invalid transitions",
        "claim-evidence-implementation bindings remain valid",
        "duplicate authority prevention",
        "replay equivalence",
    ):
        assert test_case in text


def test_sdd_preserves_security_constraints_and_traceability() -> None:
    text = read_doc()

    for security_rule in (
        "explicit identity",
        "validated inputs",
        "no undeclared runtime surfaces",
        "no direct constitutional bypass",
        "no observer-relative lifecycle mutation",
    ):
        assert security_rule in text

    for constraint in (
        "deterministic execution",
        "replay admissibility",
        "closed-world execution",
        "canonical identity resolution",
        "invariant preservation",
        "claim discipline",
    ):
        assert constraint in text

    for forbidden in (
        "redefine constitutional truth",
        "bypass replay validation",
        "create undeclared execution surfaces",
        "treat documentation as proof authority",
    ):
        assert forbidden in text

    for row in TRACEABILITY_ROWS:
        assert row in text


def test_sdd_bounds_final_classification() -> None:
    text = read_doc()

    assert "bounded operational mobility software design" in text
    assert "implemented as a Django product layer" in text
    assert "under AfriTech replay-governed constitutional admissibility constraints" in text
