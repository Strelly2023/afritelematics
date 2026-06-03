"""Entropy envelope entry point."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.runtime.entropy.admissibility import check_admissibility
from afritech.runtime.entropy.classifier import classify
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent, normalize
from afritech.runtime.entropy.recorder import EntropyRecord, record


class EntropyEnvelope:
    """Convert uncontrolled reality into replay-safe entropy evidence."""

    def __init__(self) -> None:
        self._events: list[NormalizedEntropyEvent] = []
        self._records: list[EntropyRecord] = []

    @property
    def records(self) -> tuple[EntropyRecord, ...]:
        return tuple(self._records)

    def ingest(self, raw_event: Mapping[str, Any]) -> EntropyRecord:
        normalized = self.normalize(raw_event)
        classification = self.classify(normalized)
        decision = self.check_admissibility(normalized)
        evidence = self.record(normalized, classification, decision)
        self._events.append(normalized)
        self._records.append(evidence)
        return evidence

    def normalize(self, raw_event: Mapping[str, Any]) -> NormalizedEntropyEvent:
        return normalize(raw_event)

    def classify(self, event: NormalizedEntropyEvent):
        return classify(event, prior_events=self._events)

    def check_admissibility(self, event: NormalizedEntropyEvent):
        return check_admissibility(event)

    def record(self, event, classification, decision) -> EntropyRecord:
        return record(event, classification, decision)
