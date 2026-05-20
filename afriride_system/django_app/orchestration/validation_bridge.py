"""Validation bridge for AfriRide product code.

The bridge represents a verification boundary. It records that product code
requested validation, but it does not import protected AfriTech internals,
mutate proof truth, or redefine admissibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ValidationSubject(Protocol):
    """Minimal protocol for entities that can request validation."""

    id: object
    status: str


@dataclass(frozen=True)
class ValidationReceipt:
    """Receipt emitted by the product bridge without authority escalation."""

    entity_id: str
    status: str
    bridge: str = "afriride_product_validation_bridge"
    authority: str = "non_authoritative"


def validate_execution(entity: ValidationSubject) -> ValidationReceipt:
    """Return a deterministic validation receipt for product-layer code.

    Real validator execution remains external to this product bridge and is
    enforced by the constitutional pipeline.
    """

    return ValidationReceipt(entity_id=str(entity.id), status=entity.status)
