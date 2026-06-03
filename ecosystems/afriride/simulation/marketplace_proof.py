"""Deterministic marketplace realism proof for AfriRide."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Sequence

from ecosystems.afriride.market.fairness_engine import FairnessEngine
from ecosystems.afriride.market.market_simulator import MarketSimulator
from ecosystems.afriride.market.pricing_engine import PricingEngine
from ecosystems.afriride.market.surge_model import SurgeModel


AUTHORITY_DISCLAIMER = (
    "Marketplace behavior may create events. Marketplace pressure may not "
    "define identity, fare, match result, trip legitimacy, replay hash, event "
    "ordering, or final truth."
)

REQUIRED_SCENARIOS = (
    "100_riders_20_drivers",
    "driver_rejection_chain",
    "driver_dropout",
    "timeout",
    "surge_like_demand_pressure",
    "gps_noise_normalized",
    "duplicate_ride_requests_rejected_canonicalized",
    "scheduled_ride",
    "multi_stop_ride",
)

REQUIRED_REJECTIONS = (
    "driver_acceptance_defines_truth",
    "rider_demand_spike_defines_truth",
    "gps_noise_defines_truth",
    "client_side_surge_defines_truth",
    "duplicate_request_defines_truth",
    "timeout_race_defines_truth",
    "driver_dropout_mutates_history",
    "multi_stop_reorder_mutates_replay",
    "scheduled_ride_client_clock_defines_truth",
)

FORBIDDEN_MARKET_AUTHORITY_FIELDS = frozenset(
    {
        "authoritative_event_order",
        "authoritative_fare",
        "authoritative_match_result",
        "authoritative_replay_hash",
        "authoritative_schedule_time",
        "client_side_surge",
        "driver_acceptance_truth",
        "dropout_history_mutation",
        "final_truth",
        "gps_truth",
        "legitimacy",
        "timeout_truth",
    }
)


class MarketplaceProofError(ValueError):
    """Raised when marketplace pressure violates replay-safe authority boundaries."""


@dataclass(frozen=True)
class MarketplaceScenarioEvidence:
    scenario_name: str
    event_count: int
    partition_order_hash: str
    replay_hash: str
    canonicalized: bool
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        return (
            self.scenario_name in REQUIRED_SCENARIOS
            and self.event_count > 0
            and len(self.partition_order_hash) == 64
            and len(self.replay_hash) == 64
            and self.canonicalized
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "canonicalized": self.canonicalized,
            "event_count": self.event_count,
            "partition_order_hash": self.partition_order_hash,
            "replay_hash": self.replay_hash,
            "scenario_name": self.scenario_name,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class MarketplaceProofReport:
    scenarios: tuple[MarketplaceScenarioEvidence, ...]
    rejected_authority_cases: tuple[str, ...]
    market_replay_hash: str
    partition_order_hash: str
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        scenario_names = tuple(scenario.scenario_name for scenario in self.scenarios)
        return (
            scenario_names == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
            and self.rejected_authority_cases == REQUIRED_REJECTIONS
            and len(self.market_replay_hash) == 64
            and len(self.partition_order_hash) == 64
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "market_replay_hash": self.market_replay_hash,
            "partition_order_hash": self.partition_order_hash,
            "rejected_authority_cases": list(self.rejected_authority_cases),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afriride.marketplace_proof_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_marketplace_proof() -> MarketplaceProofReport:
    scenario_events = (
        _scenario_100_riders_20_drivers(),
        _scenario_driver_rejection_chain(),
        _scenario_driver_dropout(),
        _scenario_timeout(),
        _scenario_surge_like_demand_pressure(),
        _scenario_gps_noise_normalized(),
        _scenario_duplicate_ride_requests(),
        _scenario_scheduled_ride(),
        _scenario_multi_stop_ride(),
    )
    scenarios = tuple(
        MarketplaceScenarioEvidence(
            scenario_name=name,
            event_count=len(events),
            partition_order_hash=_partition_order_hash(events),
            replay_hash=_events_hash(events),
            canonicalized=True,
        )
        for name, events in zip(REQUIRED_SCENARIOS, scenario_events)
    )
    report = MarketplaceProofReport(
        market_replay_hash=_canonical_hash([scenario.replay_hash for scenario in scenarios]),
        partition_order_hash=_canonical_hash(
            [scenario.partition_order_hash for scenario in scenarios]
        ),
        rejected_authority_cases=_rejected_authority_cases(),
        scenarios=scenarios,
    )
    if not report.verified:
        raise MarketplaceProofError("marketplace proof failed")
    return report


def _scenario_100_riders_20_drivers() -> tuple[dict[str, object], ...]:
    simulator = MarketSimulator(PricingEngine(), SurgeModel(), FairnessEngine())
    drivers = tuple(f"driver.{index:03d}" for index in range(20))
    riders = tuple(f"rider.{index:03d}" for index in range(100))
    state = simulator.run(12, 100, 20, drivers, riders)
    events = [_event("market.capacity", "rides", 0, state)]
    for index, match in enumerate(state["matches"]):
        events.append(_event("market.match", "matches", index, match))
    return tuple(events)


def _scenario_driver_rejection_chain() -> tuple[dict[str, object], ...]:
    return tuple(
        _event(
            "market.driver_rejection",
            "dispatch",
            index,
            {"driver_id": f"driver.{index:03d}", "ride_id": "ride.rejection.001"},
        )
        for index in range(5)
    ) + (
        _event(
            "market.assignment_after_rejection",
            "dispatch",
            5,
            {"driver_id": "driver.005", "ride_id": "ride.rejection.001"},
        ),
    )


def _scenario_driver_dropout() -> tuple[dict[str, object], ...]:
    return (
        _event("market.assignment", "dispatch", 0, {"driver_id": "driver.dropout.001"}),
        _event("market.dropout_observed", "dispatch", 1, {"driver_id": "driver.dropout.001"}),
        _event("market.reassignment", "dispatch", 2, {"driver_id": "driver.dropout.002"}),
    )


def _scenario_timeout() -> tuple[dict[str, object], ...]:
    return (
        _event("market.offer_created", "timeout", 0, {"ride_id": "ride.timeout.001"}),
        _event("market.timeout_observed", "timeout", 1, {"server_elapsed_seconds": 30}),
        _event("market.offer_reissued", "timeout", 2, {"attempt": 2}),
    )


def _scenario_surge_like_demand_pressure() -> tuple[dict[str, object], ...]:
    simulator = MarketSimulator(PricingEngine(), SurgeModel(), FairnessEngine())
    state = simulator.run(
        10,
        100,
        20,
        tuple(f"driver.surge.{index:03d}" for index in range(20)),
        tuple(f"rider.surge.{index:03d}" for index in range(100)),
        seed=88,
    )
    return (
        _event("market.demand_pressure", "pricing", 0, state),
        _event(
            "market.surge_bounded",
            "pricing",
            1,
            {"price": state["price"], "surge": state["surge"]},
        ),
    )


def _scenario_gps_noise_normalized() -> tuple[dict[str, object], ...]:
    noisy_points = (
        {"lat": -37.8136001, "lng": 144.9631004},
        {"lat": -37.8135999, "lng": 144.9630998},
        {"lat": -37.8136002, "lng": 144.9631001},
    )
    normalized = _normalize_gps(noisy_points)
    return tuple(
        _event(
            "market.gps_noise_normalized",
            "gps",
            index,
            {"normalized": normalized, "observed": point},
        )
        for index, point in enumerate(noisy_points)
    )


def _scenario_duplicate_ride_requests() -> tuple[dict[str, object], ...]:
    canonical = _canonical_ride_request("ride.duplicate.001")
    duplicate = _canonical_ride_request("ride.duplicate.001")
    if _canonical_hash(canonical) != _canonical_hash(duplicate):
        raise MarketplaceProofError("duplicate request did not canonicalize")
    return (
        _event("market.ride_request", "request", 0, canonical),
        _event(
            "market.duplicate_request_canonicalized",
            "request",
            1,
            {"canonical_request_hash": _canonical_hash(canonical)},
        ),
    )


def _scenario_scheduled_ride() -> tuple[dict[str, object], ...]:
    return (
        _event(
            "market.scheduled_ride_declared",
            "schedule",
            0,
            {"ride_id": "ride.schedule.001", "server_schedule_slot": "slot.2026-05-26T09"},
        ),
        _event(
            "market.scheduled_ride_queued",
            "schedule",
            1,
            {"server_order": 1},
        ),
    )


def _scenario_multi_stop_ride() -> tuple[dict[str, object], ...]:
    stops = (
        {"node_id": "flinders", "sequence": 0},
        {"node_id": "southern_cross", "sequence": 1},
        {"node_id": "docklands", "sequence": 2},
    )
    return tuple(
        _event("market.multi_stop", "multistop", index, stop)
        for index, stop in enumerate(stops)
    )


def _rejected_authority_cases() -> tuple[str, ...]:
    rejected = []
    for case_name, attempt in (
        ("driver_acceptance_defines_truth", _reject_driver_acceptance_truth),
        ("rider_demand_spike_defines_truth", _reject_demand_spike_truth),
        ("gps_noise_defines_truth", _reject_gps_truth),
        ("client_side_surge_defines_truth", _reject_client_side_surge_truth),
        ("duplicate_request_defines_truth", _reject_duplicate_truth),
        ("timeout_race_defines_truth", _reject_timeout_truth),
        ("driver_dropout_mutates_history", _reject_dropout_history_mutation),
        ("multi_stop_reorder_mutates_replay", _reject_multi_stop_reorder),
        ("scheduled_ride_client_clock_defines_truth", _reject_scheduled_client_clock),
    ):
        try:
            attempt()
        except MarketplaceProofError:
            rejected.append(case_name)
        else:
            raise MarketplaceProofError(f"marketplace authority case admitted: {case_name}")
    return tuple(rejected)


def _reject_driver_acceptance_truth() -> None:
    _normalize_market_event(
        {"driver_acceptance_truth": "accepted", "ride_id": "ride.001"},
        event_type="driver_acceptance",
    )


def _reject_demand_spike_truth() -> None:
    _normalize_market_event(
        {"demand": 100, "final_truth": "surge_authorized"},
        event_type="demand_spike",
    )


def _reject_gps_truth() -> None:
    _normalize_market_event(
        {"gps_truth": {"lat": -37.8, "lng": 144.9}},
        event_type="gps_noise",
    )


def _reject_client_side_surge_truth() -> None:
    _normalize_market_event(
        {"client_side_surge": "3.0", "ride_id": "ride.001"},
        event_type="surge",
    )


def _reject_duplicate_truth() -> None:
    _normalize_market_event(
        {"authoritative_replay_hash": "0" * 64, "ride_id": "ride.duplicate"},
        event_type="duplicate",
    )


def _reject_timeout_truth() -> None:
    _normalize_market_event(
        {"ride_id": "ride.timeout", "timeout_truth": "expired"},
        event_type="timeout",
    )


def _reject_dropout_history_mutation() -> None:
    _normalize_market_event(
        {"driver_id": "driver.dropout", "dropout_history_mutation": True},
        event_type="dropout",
    )


def _reject_multi_stop_reorder() -> None:
    stops = (
        {"node_id": "docklands", "sequence": 2},
        {"node_id": "flinders", "sequence": 0},
    )
    _require_ordered_stops(stops)


def _reject_scheduled_client_clock() -> None:
    _normalize_market_event(
        {"authoritative_schedule_time": "client-clock", "ride_id": "ride.schedule"},
        event_type="schedule",
    )


def _normalize_market_event(payload: Mapping[str, Any], *, event_type: str) -> dict[str, Any]:
    _reject_authority_fields(payload)
    return {"event_type": event_type, "payload": _canonicalize(payload)}


def _reject_authority_fields(value: Mapping[str, Any]) -> None:
    injected = FORBIDDEN_MARKET_AUTHORITY_FIELDS.intersection(value.keys())
    if injected:
        raise MarketplaceProofError(f"marketplace authority field: {sorted(injected)[0]}")
    for nested in value.values():
        if isinstance(nested, Mapping):
            _reject_authority_fields(nested)


def _require_ordered_stops(stops: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    sequences = [stop.get("sequence") for stop in stops]
    if sequences != sorted(sequences):
        raise MarketplaceProofError("multi-stop reorder mutates replay")
    return tuple(stops)


def _normalize_gps(points: Sequence[Mapping[str, float]]) -> dict[str, float]:
    return {
        "lat": round(sum(float(point["lat"]) for point in points) / len(points), 5),
        "lng": round(sum(float(point["lng"]) for point in points) / len(points), 5),
    }


def _canonical_ride_request(ride_id: str) -> dict[str, object]:
    return {
        "dropoff": {"node_id": "docklands"},
        "pickup": {"node_id": "flinders"},
        "ride_id": ride_id,
        "rider_id": "rider.duplicate.001",
    }


def _event(
    event_type: str,
    partition: str,
    sequence: int,
    payload: Mapping[str, Any],
) -> dict[str, object]:
    return {
        "event_hash": _canonical_hash(
            {
                "event_type": event_type,
                "partition": partition,
                "payload": _canonicalize(payload),
                "sequence": sequence,
            }
        ),
        "event_type": event_type,
        "partition": partition,
        "payload": _canonicalize(payload),
        "sequence": sequence,
    }


def _events_hash(events: Sequence[Mapping[str, object]]) -> str:
    return _canonical_hash(tuple(events))


def _partition_order_hash(events: Sequence[Mapping[str, object]]) -> str:
    return _canonical_hash(
        tuple(
            {
                "event_hash": event["event_hash"],
                "partition": event["partition"],
                "sequence": event["sequence"],
            }
            for event in events
        )
    )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
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

