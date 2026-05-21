"""Deterministic AfriRide driver matching engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any


SCORE_SCALE = Decimal("1000")


def _decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def score_driver(driver: Mapping[str, Any]) -> Decimal:
    """Score a recorded driver candidate without external lookups."""

    distance_km = _decimal(driver["distance_km"], "distance_km")
    rating = _decimal(driver.get("rating", 0), "rating")
    active_trips = _decimal(driver.get("active_trips", 0), "active_trips")

    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    if active_trips < 0:
        raise ValueError("active_trips must be non-negative")

    return (-distance_km * SCORE_SCALE) + (rating * Decimal("10")) - (
        active_trips * Decimal("5")
    )


def match_driver(
    request: Mapping[str, Any],
    drivers: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a replay-stable driver assignment and full ranking."""

    if not drivers:
        raise ValueError("Driver matching requires at least one candidate")

    request_id = str(request["request_id"])
    ranked: list[dict[str, Any]] = []

    for driver in drivers:
        driver_id = str(driver["driver_id"])
        score = score_driver(driver)
        ranked.append(
            {
                "driver_id": driver_id,
                "score": str(score.normalize()),
                "distance_km": str(_decimal(driver["distance_km"], "distance_km").normalize()),
                "rating": str(_decimal(driver.get("rating", 0), "rating").normalize()),
                "active_trips": str(
                    _decimal(driver.get("active_trips", 0), "active_trips").normalize()
                ),
            }
        )

    ranked.sort(
        key=lambda candidate: (
            _decimal(candidate["score"], "score"),
            candidate["driver_id"],
        ),
        reverse=True,
    )

    return {
        "request_id": request_id,
        "selected_driver_id": ranked[0]["driver_id"],
        "ranking": ranked,
        "matching_policy": "distance_rating_active_trips_v1",
    }
