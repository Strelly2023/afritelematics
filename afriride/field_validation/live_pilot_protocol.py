"""Controlled live pilot protocol for AfriRide.

This artifact prepares real-world validation. It does not certify that a pilot
has occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


CORE_LAW = "Modeled guarantees must not degrade under physical constraints."

AUTHORITY_BOUNDARY = (
    "The live pilot protocol schedules evidence collection only. It does not "
    "define truth, certify production readiness, or claim completed deployment."
)

NON_CLAIMS = (
    "public_launch_readiness",
    "production_reliability",
    "regulatory_approval",
    "market_validation",
    "internet_scale_resilience",
    "completed_real_world_pilot",
)

REQUIRED_SCENARIOS = (
    "offline_trip",
    "delayed_sync",
    "gps_drift",
    "duplicate_events",
    "dispute_resolution",
)

REQUIRED_OUTPUTS = (
    "offline_trip.json",
    "delayed_sync.json",
    "gps_drift.json",
    "duplicate_events.json",
    "dispute_resolution.json",
    "field_equivalence.json",
    "proof_dashboard.json",
    "pilot_trace_manifest.json",
)


class LivePilotProtocolError(ValueError):
    """Raised when a live pilot protocol exceeds its claim boundary."""


@dataclass(frozen=True)
class PilotScale:
    drivers_min: int = 5
    drivers_max: int = 20
    riders_min: int = 10
    riders_max: int = 60
    pilot_days_min: int = 3
    pilot_days_max: int = 14

    def __post_init__(self) -> None:
        if not (5 <= self.drivers_min <= self.drivers_max <= 20):
            raise LivePilotProtocolError("driver count must remain within 5-20")
        if self.riders_min <= 0 or self.riders_max < self.riders_min:
            raise LivePilotProtocolError("rider range must be bounded and positive")
        if self.pilot_days_min <= 0 or self.pilot_days_max < self.pilot_days_min:
            raise LivePilotProtocolError("pilot duration must be bounded and positive")

    def canonical_dict(self) -> dict[str, int]:
        return {
            "drivers_max": self.drivers_max,
            "drivers_min": self.drivers_min,
            "pilot_days_max": self.pilot_days_max,
            "pilot_days_min": self.pilot_days_min,
            "riders_max": self.riders_max,
            "riders_min": self.riders_min,
        }


@dataclass(frozen=True)
class PilotProtocol:
    scale: PilotScale
    authority_boundary: str = AUTHORITY_BOUNDARY
    core_law: str = CORE_LAW
    non_claims: tuple[str, ...] = NON_CLAIMS
    required_scenarios: tuple[str, ...] = REQUIRED_SCENARIOS
    required_outputs: tuple[str, ...] = REQUIRED_OUTPUTS

    def __post_init__(self) -> None:
        if self.authority_boundary != AUTHORITY_BOUNDARY:
            raise LivePilotProtocolError("pilot protocol authority boundary mismatch")
        if self.core_law != CORE_LAW:
            raise LivePilotProtocolError("pilot protocol core law mismatch")
        missing_non_claims = set(NON_CLAIMS).difference(self.non_claims)
        if missing_non_claims:
            raise LivePilotProtocolError(
                f"pilot protocol missing non-claims: {tuple(sorted(missing_non_claims))}"
            )
        if self.required_scenarios != REQUIRED_SCENARIOS:
            raise LivePilotProtocolError("pilot protocol scenarios are incomplete")
        if self.required_outputs != REQUIRED_OUTPUTS:
            raise LivePilotProtocolError("pilot protocol outputs are incomplete")

    @property
    def protocol_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "authority_boundary": self.authority_boundary,
            "claim_boundary": {
                "allowed_claim": (
                    "AfriRide is approved to collect bounded real-pilot evidence "
                    "for Gates 1-7 and field-validation reproducibility."
                ),
                "non_claims": list(self.non_claims),
            },
            "core_law": self.core_law,
            "device_plan": _device_plan(),
            "evidence_outputs": list(self.required_outputs),
            "metrics": _metrics(),
            "operator_roles": _operator_roles(),
            "pilot_phases": _pilot_phases(),
            "scenario_scripts": _scenario_scripts(),
            "schema": "afriride.live_pilot_protocol.v1",
            "scale": self.scale.canonical_dict(),
            "stop_conditions": _stop_conditions(),
        }
        if include_hash:
            payload["protocol_hash"] = self.protocol_hash
        return payload


def build_live_pilot_protocol() -> PilotProtocol:
    return PilotProtocol(scale=PilotScale())


def write_live_pilot_protocol(
    output_path: str | Path = "reports/afriride_live_pilot_protocol_v1/live_pilot_protocol.json",
) -> PilotProtocol:
    protocol = build_live_pilot_protocol()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(protocol.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return protocol


def _operator_roles() -> tuple[dict[str, object], ...]:
    return (
        {
            "role": "pilot_controller",
            "count": 1,
            "duties": (
                "opens and closes pilot windows",
                "enforces stop conditions",
                "approves evidence package submission",
            ),
        },
        {
            "role": "proof_operator",
            "count": 1,
            "duties": (
                "runs replay validators",
                "publishes proof dashboard artifacts",
                "records hash commitments",
            ),
        },
        {
            "role": "support_operator",
            "count": 2,
            "duties": (
                "captures rider and driver dispute reports",
                "routes disputes through replay authority",
                "blocks manual truth overrides",
            ),
        },
        {
            "role": "safety_observer",
            "count": 1,
            "duties": (
                "monitors non-computational rider and driver safety",
                "can stop field activity without changing proof truth",
            ),
        },
    )


def _device_plan() -> dict[str, object]:
    return {
        "driver_devices": {
            "count": "5-20",
            "requirements": (
                "signed event emission",
                "offline event buffer",
                "GPS observation capture",
                "logical clock",
                "connectivity transition logs",
            ),
        },
        "rider_devices": {
            "count": "10-60",
            "requirements": (
                "signed request events",
                "pickup and dropoff confirmation events",
                "dispute submission event",
                "projection-only ride status view",
            ),
        },
        "operations_devices": {
            "count": 2,
            "requirements": (
                "trace inspection",
                "validator execution",
                "incident logging",
            ),
        },
    }


def _pilot_phases() -> tuple[dict[str, object], ...]:
    return (
        {
            "phase": "preflight",
            "exit_rule": "all devices registered and dry-run traces replay cleanly",
            "minimum_runs": 5,
        },
        {
            "phase": "shadow_trips",
            "exit_rule": "field traces match simulated baselines without live riders",
            "minimum_runs": 10,
        },
        {
            "phase": "controlled_live_trips",
            "exit_rule": "all required scenarios pass with real driver/rider flow",
            "minimum_runs": 20,
        },
        {
            "phase": "dispute_drills",
            "exit_rule": "support disputes resolve from replay authority only",
            "minimum_runs": 5,
        },
        {
            "phase": "evidence_review",
            "exit_rule": "pilot trace manifest and proof dashboard are hash-bound",
            "minimum_runs": 1,
        },
    )


def _scenario_scripts() -> tuple[dict[str, object], ...]:
    return (
        {
            "scenario": "offline_trip",
            "script": (
                "driver accepts ride, disconnects mid-trip, buffers events locally, "
                "reconnects, syncs through normalization, and replay is compared"
            ),
            "must_produce": ("offline_trip.json", "pilot_trace_manifest.json"),
        },
        {
            "scenario": "delayed_sync",
            "script": (
                "driver and rider events are held for delayed delivery, then "
                "submitted after the trip boundary and replayed in canonical order"
            ),
            "must_produce": ("delayed_sync.json", "field_equivalence.json"),
        },
        {
            "scenario": "gps_drift",
            "script": (
                "real GPS jitter, loss, and implausible jumps are captured as "
                "observations and normalized without changing pricing truth"
            ),
            "must_produce": ("gps_drift.json", "proof_dashboard.json"),
        },
        {
            "scenario": "duplicate_events",
            "script": (
                "same signed event batch is sent more than once and must not "
                "produce duplicate execution"
            ),
            "must_produce": ("duplicate_events.json", "field_equivalence.json"),
        },
        {
            "scenario": "dispute_resolution",
            "script": (
                "rider or driver submits a conflicting claim and support resolves "
                "it through replay authority without manual truth override"
            ),
            "must_produce": ("dispute_resolution.json", "proof_dashboard.json"),
        },
    )


def _metrics() -> dict[str, object]:
    return {
        "admissibility_divergence": 0,
        "authentication_bypass": 0,
        "dispute_reproducibility_rate": 1.0,
        "identity_divergence": 0,
        "pricing_deviation": 0,
        "replay_equivalence_rate": 1.0,
        "trace_completeness_rate": 1.0,
    }


def _stop_conditions() -> tuple[str, ...]:
    return (
        "replay mismatch",
        "identity inconsistency",
        "pricing deviation",
        "admissibility divergence",
        "dispute mismatch",
        "authentication bypass",
        "missing mandatory lifecycle events",
        "manual truth override attempted",
        "pilot scope escape",
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
