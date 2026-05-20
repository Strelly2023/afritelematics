"""Driver model skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar
from uuid import UUID, uuid4


@dataclass
class Driver:
    name: str
    is_available: bool = True
    id: UUID = field(default_factory=uuid4)

    objects: ClassVar["DriverManager"]


class DriverQuery:
    def __init__(self, drivers: tuple[Driver, ...]) -> None:
        self._drivers = drivers

    def first(self) -> Driver | None:
        return self._drivers[0] if self._drivers else None


class DriverManager:
    def __init__(self) -> None:
        self._items: list[Driver] = []

    def create(self, **kwargs: object) -> Driver:
        driver = Driver(**kwargs)
        self._items.append(driver)
        return driver

    def filter(self, *, is_available: bool) -> DriverQuery:
        matches = tuple(driver for driver in self._items if driver.is_available is is_available)
        return DriverQuery(matches)

    def clear(self) -> None:
        self._items.clear()


Driver.objects = DriverManager()
