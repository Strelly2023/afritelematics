"""Replay-validated evidence store for AfriRide proof artifacts.

Storage is evidence, not truth. Writes and reads both validate by replay before
returning a stored bundle to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from ecosystems.afriride.domain.execution.ride_execution_engine import RideExecutionStep
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import DriverAssignment
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricePlan,
    PricingConfig,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import RoutePlan
from ecosystems.afriride.domain.replay.ride_replay_validator import (
    RideReplayReport,
    RideReplayViolation,
    validate_ride_replay,
)
from ecosystems.afriride.domain.trace.ride_execution_trace import RideExecutionTrace


class EvidenceStoreViolation(ValueError):
    """Raised when stored evidence cannot prove itself through replay."""


@dataclass(frozen=True)
class RideEvidenceBundle:
    """Complete replay input snapshot for one traced ride."""

    ride: Ride
    trace: RideExecutionTrace
    drivers: tuple[Mapping[str, Any], ...] = ()
    map_graph: Mapping[str, Any] | None = None
    pricing_config: PricingConfig | None = None
    assignment: DriverAssignment | None = None
    route: RoutePlan | None = None
    price: PricePlan | None = None
    execution_steps: tuple[RideExecutionStep, ...] = ()

    def trace_hash(self) -> str:
        """Return the canonical lookup key for this evidence bundle."""

        return self.trace.trace_hash()

    def canonical_summary(self) -> dict[str, Any]:
        """Return a deterministic evidence summary for callers."""

        return {
            "assignment_hash": (
                self.assignment.assignment_hash() if self.assignment else None
            ),
            "execution_steps_hash": self.trace.execution_steps_hash,
            "price_hash": self.price.price_hash() if self.price else None,
            "ride_hash": self.ride.ride_hash(),
            "route_hash": self.route.route_hash() if self.route else None,
            "trace_hash": self.trace_hash(),
        }


@dataclass(frozen=True)
class VerifiedRideEvidence:
    """Evidence returned only after replay validation."""

    bundle: RideEvidenceBundle
    replay_report: RideReplayReport


class InMemoryRideEvidenceStore:
    """In-memory evidence store with replay-on-write and replay-on-read."""

    def __init__(self) -> None:
        self._records: dict[str, RideEvidenceBundle] = {}

    def store(self, bundle: RideEvidenceBundle) -> str:
        """Validate and store an evidence bundle by trace hash."""

        report = self._validate(bundle)
        trace_hash = bundle.trace_hash()
        if trace_hash in self._records:
            raise EvidenceStoreViolation("evidence already exists for trace_hash")
        self._records[trace_hash] = bundle
        if not report.replay_valid:
            raise EvidenceStoreViolation("evidence replay validation failed")
        return trace_hash

    def get(self, trace_hash: str) -> VerifiedRideEvidence:
        """Load evidence only after replay validation succeeds."""

        if trace_hash not in self._records:
            raise EvidenceStoreViolation("evidence not found")
        bundle = self._records[trace_hash]
        report = self._validate(bundle)
        return VerifiedRideEvidence(bundle=bundle, replay_report=report)

    def list_trace_hashes(self) -> tuple[str, ...]:
        """Return stored trace hashes without asserting truth about contents."""

        return tuple(sorted(self._records))

    def corrupt_for_test(self, trace_hash: str, **changes: Any) -> None:
        """Replace stored evidence for tests; read path must still replay."""

        if trace_hash not in self._records:
            raise EvidenceStoreViolation("evidence not found")
        self._records[trace_hash] = replace(self._records[trace_hash], **changes)

    def _validate(self, bundle: RideEvidenceBundle) -> RideReplayReport:
        try:
            return validate_ride_replay(
                bundle.trace,
                bundle.ride,
                drivers=bundle.drivers or None,
                map_graph=bundle.map_graph,
                pricing_config=bundle.pricing_config,
                execution_steps=bundle.execution_steps,
            )
        except RideReplayViolation as exc:
            raise EvidenceStoreViolation(str(exc)) from exc
