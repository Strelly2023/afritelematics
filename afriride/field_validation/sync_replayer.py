"""Replay field traces against the modeled baseline truth."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.convergence import ConvergenceResult, converge


OBSERVATIONAL_ACTIONS = frozenset({"gps_update", "network_status"})


@dataclass(frozen=True)
class FieldReplayResult:
    baseline: ConvergenceResult
    field: ConvergenceResult
    field_authoritative_trace: tuple[Mapping[str, Any], ...]
    observed_event_count: int

    @property
    def replay_match(self) -> bool:
        return self.baseline.replay_hash == self.field.replay_hash

    @property
    def identity_match(self) -> bool:
        return self.baseline.identity_resolution_hash == self.field.identity_resolution_hash

    @property
    def admissibility_match(self) -> bool:
        return self.baseline.admissibility_hash == self.field.admissibility_hash

    @property
    def convergence_match(self) -> bool:
        return self.baseline.convergence_hash == self.field.convergence_hash

    @property
    def pricing_match(self) -> bool:
        return _fare(self.baseline) == _fare(self.field)

    @property
    def verified(self) -> bool:
        return (
            self.replay_match
            and self.identity_match
            and self.admissibility_match
            and self.convergence_match
            and self.pricing_match
        )

    @property
    def field_replay_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "admissibility_match": self.admissibility_match,
            "baseline": self.baseline.canonical_dict(),
            "convergence_match": self.convergence_match,
            "field": self.field.canonical_dict(),
            "field_authoritative_trace": [
                _canonicalize(event) for event in self.field_authoritative_trace
            ],
            "identity_match": self.identity_match,
            "observed_event_count": self.observed_event_count,
            "pricing_match": self.pricing_match,
            "replay_match": self.replay_match,
            "verified": self.verified,
        }
        if include_hash:
            payload["field_replay_hash"] = self.field_replay_hash
        return payload


def replay_field_trace(
    baseline_trace: Iterable[Mapping[str, Any]],
    field_trace: Iterable[Mapping[str, Any]],
) -> FieldReplayResult:
    baseline = tuple(baseline_trace)
    field = tuple(field_trace)
    authoritative = _authoritative_trace(field)
    return FieldReplayResult(
        baseline=converge(baseline),
        field=converge(authoritative),
        field_authoritative_trace=authoritative,
        observed_event_count=len(field),
    )


def _authoritative_trace(
    field_trace: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    by_event_id: dict[str, Mapping[str, Any]] = {}
    for event in field_trace:
        payload = event.get("payload", {})
        action = payload.get("action") if isinstance(payload, Mapping) else None
        if action in OBSERVATIONAL_ACTIONS:
            continue
        by_event_id[str(event["event_id"])] = event
    return tuple(
        by_event_id[key]
        for key in sorted(
            by_event_id,
            key=lambda item: (
                int(by_event_id[item].get("sequence", 0)),
                item,
            ),
        )
    )


def _fare(result: ConvergenceResult) -> int | None:
    for event in result.accepted_events:
        if event.payload.get("action") == "price_quote":
            return int(event.payload.get("fare_cents", 0))
    return None


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

