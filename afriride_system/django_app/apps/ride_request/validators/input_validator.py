"""Input validation for ride requests."""

from __future__ import annotations

from typing import Any


class RideRequestValidator:
    """Validate required ride request fields."""

    REQUIRED = ("rider_id", "origin", "destination")

    @staticmethod
    def validate(data: dict[str, Any]) -> None:
        for field in RideRequestValidator.REQUIRED:
            if field not in data:
                raise ValueError(f"Missing field: {field}")
