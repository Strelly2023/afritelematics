"""Disturbance classification for entropy-bound execution."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent


class DisturbanceType(str, Enum):
    NORMAL = "normal"
    DUPLICATE = "duplicate"
    DELAYED = "delayed"
    OUT_OF_ORDER = "out_of_order"
    PARTITIONED = "partitioned"
    CORRUPTED = "corrupted"
    CLOCK_DRIFT = "clock_drift"
    OFFLINE_RECOVERY = "offline_recovery"


def classify(
    event: NormalizedEntropyEvent,
    *,
    prior_events: Iterable[NormalizedEntropyEvent] = (),
) -> DisturbanceType:
    prior = tuple(prior_events)
    if event.corrupted:
        return DisturbanceType.CORRUPTED
    if any(existing.canonical_id == event.canonical_id for existing in prior):
        return DisturbanceType.DUPLICATE
    if event.source == "offline_recovery":
        return DisturbanceType.OFFLINE_RECOVERY
    if event.partition_id != _canonical_partition(event.identity_id):
        return DisturbanceType.PARTITIONED
    if event.normalized_timestamp.startswith("drift:"):
        return DisturbanceType.CLOCK_DRIFT
    if prior and event.sequence < max(existing.sequence for existing in prior):
        return DisturbanceType.OUT_OF_ORDER
    if event.received_order < event.sequence:
        return DisturbanceType.OUT_OF_ORDER
    if event.received_order > event.sequence:
        return DisturbanceType.DELAYED
    return DisturbanceType.NORMAL


def _canonical_partition(identity_id: str) -> str:
    return f"partition.{sum(identity_id.encode('utf-8')) % 4}"
