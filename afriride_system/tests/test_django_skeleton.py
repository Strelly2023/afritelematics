from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid4

import pytest

from afriride_system.django_app.apps.driver.models import Driver
from afriride_system.django_app.apps.ride_lifecycle.domain.entities import RideState
from afriride_system.django_app.apps.ride_lifecycle.services.lifecycle_service import (
    RideLifecycleService,
)
from afriride_system.django_app.apps.ride_matching.services.matching_service import (
    MatchingService,
)
from afriride_system.django_app.apps.ride_request.models import RideIntent
from afriride_system.django_app.apps.ride_request.services.ride_request_service import (
    RideRequestService,
)
from afriride_system.django_app.apps.ride_request.validators.input_validator import (
    RideRequestValidator,
)
from afriride_system.django_app.apps.pricing.services.pricing_service import PricingService
from afriride_system.django_app.apps.safety.services.safety_service import SafetyService


ROOT = Path(__file__).resolve().parents[2]
SKELETON = ROOT / "afriride_system/django_app"

EXPECTED_PATHS = (
    "manage.py",
    "core/settings/base.py",
    "core/urls.py",
    "apps/ride_request/models/ride_intent.py",
    "apps/ride_request/services/ride_request_service.py",
    "apps/ride_request/validators/input_validator.py",
    "apps/ride_lifecycle/domain/entities.py",
    "apps/ride_lifecycle/services/lifecycle_service.py",
    "apps/pricing/services/pricing_service.py",
    "apps/ride_matching/services/matching_service.py",
    "apps/rider/models/rider.py",
    "apps/driver/models/driver.py",
    "apps/safety/services/safety_service.py",
    "api/v1/ride/views.py",
    "api/v1/ride/urls.py",
    "orchestration/validation_bridge.py",
    "interfaces/dto/ride.py",
    "interfaces/schemas/ride_schema.py",
)

PROTECTED_IMPORT_PREFIXES = (
    "afritech.demo",
    "afritech.ci",
    "afritech.constitution",
)

PROTECTED_PATH_PARTS = (
    ("afritech", "demo", "proof.py"),
    ("afritech", "constitution", "FIVE_INVARIANT_CONTRACT.yaml"),
    ("afritech", "ci", "four_gate_validator.py"),
    ("afritech", "ci", "enforcement_integrity_validator.py"),
    ("afritech", "ci", "constitutional_validation.py"),
    ("afritech", "ci", "constitutional_pipeline.py"),
)


@pytest.fixture(autouse=True)
def clear_memory_managers() -> None:
    RideIntent.objects.clear()
    Driver.objects.clear()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_django_skeleton_expected_files_exist() -> None:
    for relative in EXPECTED_PATHS:
        assert (SKELETON / relative).exists(), relative


def test_ride_request_service_creates_requested_ride_with_non_authoritative_receipt() -> None:
    rider_id = uuid4()
    ride, receipt = RideRequestService.create_ride_intent(
        {
            "rider_id": rider_id,
            "origin": {"lat": 1, "lng": 1},
            "destination": {"lat": 2, "lng": 2},
        }
    )

    assert ride.rider_id == rider_id
    assert ride.status == RideState.REQUESTED
    assert receipt.entity_id == str(ride.id)
    assert receipt.status == RideState.REQUESTED
    assert receipt.authority == "non_authoritative"


def test_ride_request_validator_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="Missing field: destination"):
        RideRequestValidator.validate(
            {
                "rider_id": uuid4(),
                "origin": {"lat": 1, "lng": 1},
            }
        )


def test_lifecycle_service_allows_forward_transitions_and_rejects_backward_motion() -> None:
    ride, _ = RideRequestService.create_ride_intent(
        {
            "rider_id": uuid4(),
            "origin": {"lat": 1, "lng": 1},
            "destination": {"lat": 2, "lng": 2},
        }
    )

    RideLifecycleService.transition(ride, RideState.MATCHED)
    RideLifecycleService.transition(ride, RideState.ACCEPTED)
    assert ride.status == RideState.ACCEPTED

    with pytest.raises(ValueError, match="cannot move backward"):
        RideLifecycleService.transition(ride, RideState.REQUESTED)


def test_pricing_service_is_deterministic_and_rejects_negative_distance() -> None:
    assert PricingService.calculate(10.0) == 20.0
    assert PricingService.calculate(10.0) == 20.0

    with pytest.raises(ValueError, match="non-negative"):
        PricingService.calculate(-1.0)


def test_matching_service_assigns_first_available_driver_deterministically() -> None:
    unavailable = Driver.objects.create(name="Offline", is_available=False)
    first = Driver.objects.create(name="First", is_available=True)
    second = Driver.objects.create(name="Second", is_available=True)

    assert unavailable.name == "Offline"
    assert MatchingService.assign_driver() == first
    assert MatchingService.assign_driver() != second


def test_safety_pin_is_deterministic_placeholder() -> None:
    assert SafetyService.generate_pin() == "1234"
    assert SafetyService.generate_pin() == "1234"


def test_skeleton_does_not_import_or_reference_protected_surfaces() -> None:
    for path in sorted(SKELETON.rglob("*.py")):
        modules = imported_modules(path)
        for module in modules:
            assert not module.startswith(PROTECTED_IMPORT_PREFIXES), (
                path.relative_to(ROOT),
                module,
            )

        text = path.read_text(encoding="utf-8")
        for token in ("/".join(parts) for parts in PROTECTED_PATH_PARTS):
            assert token not in text, (path.relative_to(ROOT), token)
