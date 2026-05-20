"""Ride DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RideIntentDTO:
    rider_id: UUID
    origin: dict[str, Any]
    destination: dict[str, Any]
