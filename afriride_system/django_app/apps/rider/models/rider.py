"""Rider model skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Rider:
    name: str
    phone: str
    id: UUID = field(default_factory=uuid4)
