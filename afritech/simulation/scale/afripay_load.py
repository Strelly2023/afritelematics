"""AfriPay load simulation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.afripay.events import canonical_hash
from afritech.simulation.scale.load_generator import generate_events


@dataclass(frozen=True)
class AfriPayLoadReport:
    target_tps: int
    duration_seconds: int
    worker_count: int
    event_count: int
    routing_space: int
    checksum: str


def simulate_afripay_tps(
    target_tps: int = 10000,
    *,
    duration_seconds: int = 1,
    worker_count: int = 16,
) -> AfriPayLoadReport:
    if target_tps <= 0:
        raise ValueError("target_tps must be > 0")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")
    if worker_count <= 0:
        raise ValueError("worker_count must be > 0")

    event_count = target_tps * duration_seconds
    routing_space = max(8, worker_count * 4)
    events = generate_events(event_count, routing_space=routing_space, payload_variation=8)
    checksum = canonical_hash(events)
    return AfriPayLoadReport(
        target_tps=target_tps,
        duration_seconds=duration_seconds,
        worker_count=worker_count,
        event_count=len(events),
        routing_space=routing_space,
        checksum=checksum,
    )
