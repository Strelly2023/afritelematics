"""Ride intent model for the isolated AfriRide product layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import UUID, uuid4


@dataclass
class RideIntent:
    """Django-compatible domain skeleton for a rider trip request."""

    rider_id: UUID
    origin: dict[str, Any]
    destination: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    status: str = "REQUESTED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    objects: ClassVar["RideIntentManager"]

    def save(self) -> "RideIntent":
        RideIntent.objects.upsert(self)
        return self

    def __str__(self) -> str:
        return f"RideIntent({self.id})"


class RideIntentManager:
    """Small in-memory manager used until real Django persistence is added."""

    def __init__(self) -> None:
        self._items: list[RideIntent] = []

    def create(self, **kwargs: Any) -> RideIntent:
        ride = RideIntent(**kwargs)
        self._items.append(ride)
        return ride

    def upsert(self, ride: RideIntent) -> None:
        for index, item in enumerate(self._items):
            if item.id == ride.id:
                self._items[index] = ride
                return
        self._items.append(ride)

    def all(self) -> tuple[RideIntent, ...]:
        return tuple(self._items)

    def clear(self) -> None:
        self._items.clear()


RideIntent.objects = RideIntentManager()
