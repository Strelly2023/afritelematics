"""Small ORM-style row mapper for core platform trust packets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from afritech.core_platform.models import CorePlatformFlowResult


@dataclass(frozen=True)
class CoreTrustPacketRecord:
    id: str
    receipt_id: str | None
    organization_id: str
    event_type: str
    packet: Mapping[str, Any]

    @classmethod
    def from_flow(cls, result: CorePlatformFlowResult) -> "CoreTrustPacketRecord":
        return cls(
            id=result.trust.trust_id,
            receipt_id=result.payment.receipt_id if result.payment else None,
            organization_id=result.trust.organization_id,
            event_type=result.trust.event_type,
            packet=result.canonical(),
        )

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> "CoreTrustPacketRecord":
        packet = row[4]
        if isinstance(packet, str):
            packet = json.loads(packet)
        return cls(
            id=str(row[0]),
            receipt_id=str(row[1]) if row[1] is not None else None,
            organization_id=str(row[2]),
            event_type=str(row[3]),
            packet=dict(packet),
        )

    def insert_params(self) -> tuple[str, str | None, str, str, str]:
        return (
            self.id,
            self.receipt_id,
            self.organization_id,
            self.event_type,
            json.dumps(dict(self.packet), sort_keys=True),
        )
