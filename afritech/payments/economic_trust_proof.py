"""Economic trust proof for replay-governed value-transfer events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Callable, Mapping


AUTHORITY_DISCLAIMER = (
    "Economic systems may authorize, settle, refund, split, and record "
    "value-transfer events. Economic systems may not define trip legitimacy, "
    "replay truth, fare truth, event ordering, commission truth, refund truth, "
    "or final authority."
)

REQUIRED_PROOFS = (
    "deterministic_fare_calculation",
    "payment_authorization_isolated",
    "refund_event_replayable",
    "fare_split_replayable",
    "commission_calculation_deterministic",
    "payment_provider_non_authoritative",
)

REQUIRED_REJECTIONS = (
    "provider_authorization_defines_trip_truth",
    "provider_timestamp_defines_event_order",
    "provider_fare_overrides_canonical_fare",
    "client_fare_defines_truth",
    "driver_commission_override_accepted",
    "refund_mutation_rewrites_history",
    "fare_split_imbalance_accepted",
    "duplicate_payment_event_defines_truth",
)

FORBIDDEN_ECONOMIC_AUTHORITY_FIELDS = frozenset(
    {
        "authoritative_commission",
        "authoritative_event_order",
        "authoritative_fare",
        "authoritative_refund",
        "client_fare_truth",
        "final_authority",
        "provider_authorization_truth",
        "provider_timestamp_truth",
        "replay_truth",
        "trip_legitimacy",
    }
)


class EconomicTrustProofError(ValueError):
    """Raised when economic proof violates replay-safe authority boundaries."""


@dataclass(frozen=True)
class FarePlan:
    ride_id: str
    distance_km: Decimal
    duration_minutes: Decimal
    base_fare: Decimal
    per_km_rate: Decimal
    per_minute_rate: Decimal
    currency: str = "AUD"

    def __post_init__(self) -> None:
        object.__setattr__(self, "ride_id", _require_text(self.ride_id, "ride_id"))
        object.__setattr__(self, "distance_km", _money(self.distance_km))
        object.__setattr__(self, "duration_minutes", _money(self.duration_minutes))
        object.__setattr__(self, "base_fare", _money(self.base_fare))
        object.__setattr__(self, "per_km_rate", _money(self.per_km_rate))
        object.__setattr__(self, "per_minute_rate", _money(self.per_minute_rate))
        object.__setattr__(self, "currency", _require_text(self.currency, "currency"))

    @property
    def total_fare(self) -> Decimal:
        return _money(
            self.base_fare
            + (self.distance_km * self.per_km_rate)
            + (self.duration_minutes * self.per_minute_rate)
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "base_fare": _decimal_text(self.base_fare),
            "currency": self.currency,
            "distance_km": _decimal_text(self.distance_km),
            "duration_minutes": _decimal_text(self.duration_minutes),
            "fare_basis": "base_plus_distance_plus_time",
            "per_km_rate": _decimal_text(self.per_km_rate),
            "per_minute_rate": _decimal_text(self.per_minute_rate),
            "ride_id": self.ride_id,
            "total_fare": _decimal_text(self.total_fare),
        }

    def fare_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class EconomicEvent:
    event_id: str
    event_type: str
    ride_id: str
    sequence: int
    payload: Mapping[str, Any]
    canonical_fare_hash: str
    provider_reference: str | None = None
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    def __post_init__(self) -> None:
        _require_text(self.event_id, "event_id")
        _require_text(self.event_type, "event_type")
        _require_text(self.ride_id, "ride_id")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise EconomicTrustProofError("sequence must be non-negative int")
        if not isinstance(self.payload, Mapping):
            raise EconomicTrustProofError("payload must be mapping")
        _require_hash(self.canonical_fare_hash, "canonical_fare_hash")
        if self.provider_reference is not None:
            _require_text(self.provider_reference, "provider_reference")
        if self.authority_disclaimer != AUTHORITY_DISCLAIMER:
            raise EconomicTrustProofError("economic authority disclaimer mismatch")
        _reject_authority_fields(self.payload)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "canonical_fare_hash": self.canonical_fare_hash,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": _canonicalize(self.payload),
            "provider_reference": self.provider_reference,
            "ride_id": self.ride_id,
            "sequence": self.sequence,
        }

    def event_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class EconomicTrustProofReport:
    proof_names: tuple[str, ...]
    rejected_cases: tuple[str, ...]
    fare_hash: str
    authorization_event_hash: str
    refund_event_hash: str
    split_hash: str
    commission_hash: str
    economic_replay_hash: str
    provider_non_authoritative: bool
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        return (
            self.proof_names == REQUIRED_PROOFS
            and self.rejected_cases == REQUIRED_REJECTIONS
            and self.provider_non_authoritative
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and all(len(value) == 64 for value in self._hashes())
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "authorization_event_hash": self.authorization_event_hash,
            "commission_hash": self.commission_hash,
            "economic_replay_hash": self.economic_replay_hash,
            "fare_hash": self.fare_hash,
            "proof_names": list(self.proof_names),
            "provider_non_authoritative": self.provider_non_authoritative,
            "refund_event_hash": self.refund_event_hash,
            "rejected_cases": list(self.rejected_cases),
            "schema": "afritech.economic_trust_proof_report.v1",
            "split_hash": self.split_hash,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())

    def _hashes(self) -> tuple[str, ...]:
        return (
            self.fare_hash,
            self.authorization_event_hash,
            self.refund_event_hash,
            self.split_hash,
            self.commission_hash,
            self.economic_replay_hash,
        )


def run_economic_trust_proof() -> EconomicTrustProofReport:
    fare = FarePlan(
        ride_id="ride.economic.001",
        distance_km=Decimal("12.40"),
        duration_minutes=Decimal("28.00"),
        base_fare=Decimal("4.20"),
        per_km_rate=Decimal("1.70"),
        per_minute_rate=Decimal("0.45"),
    )
    authorization = _payment_authorization_event(fare)
    refund = _refund_event(fare)
    split = _fare_split(fare)
    commission = _commission(fare)
    report = EconomicTrustProofReport(
        authorization_event_hash=authorization.event_hash(),
        commission_hash=_canonical_hash(commission),
        economic_replay_hash=_canonical_hash(
            (
                authorization.canonical_dict(),
                refund.canonical_dict(),
                split,
                commission,
            )
        ),
        fare_hash=fare.fare_hash(),
        proof_names=REQUIRED_PROOFS,
        provider_non_authoritative=_provider_non_authoritative(authorization, fare),
        refund_event_hash=refund.event_hash(),
        rejected_cases=_rejected_cases(),
        split_hash=_canonical_hash(split),
    )
    if not report.verified:
        raise EconomicTrustProofError("economic trust proof failed")
    return report


def _payment_authorization_event(fare: FarePlan) -> EconomicEvent:
    provider_reference = _provider_reference(fare)
    return EconomicEvent(
        canonical_fare_hash=fare.fare_hash(),
        event_id="economic.authorization.001",
        event_type="PAYMENT_AUTHORIZATION_OBSERVED",
        payload={
            "amount": _decimal_text(fare.total_fare),
            "currency": fare.currency,
            "provider": "pilot_provider",
            "provider_status": "authorized",
        },
        provider_reference=provider_reference,
        ride_id=fare.ride_id,
        sequence=0,
    )


def _refund_event(fare: FarePlan) -> EconomicEvent:
    refund_amount = _money(fare.total_fare / Decimal("2"))
    return EconomicEvent(
        canonical_fare_hash=fare.fare_hash(),
        event_id="economic.refund.001",
        event_type="REFUND_RECORDED",
        payload={
            "amount": _decimal_text(refund_amount),
            "currency": fare.currency,
            "refund_basis": "partial_service_adjustment",
        },
        provider_reference="provider.refund.observed.001",
        ride_id=fare.ride_id,
        sequence=1,
    )


def _fare_split(fare: FarePlan) -> dict[str, object]:
    driver_share = _money(fare.total_fare * Decimal("0.80"))
    platform_share = _money(fare.total_fare - driver_share)
    split = {
        "driver_share": _decimal_text(driver_share),
        "fare_hash": fare.fare_hash(),
        "platform_share": _decimal_text(platform_share),
        "total": _decimal_text(fare.total_fare),
    }
    _require_balanced_split(split)
    return split


def _commission(fare: FarePlan) -> dict[str, object]:
    commission = _money(fare.total_fare * Decimal("0.20"))
    return {
        "commission_basis": "canonical_fare_x_20_percent",
        "commission": _decimal_text(commission),
        "fare_hash": fare.fare_hash(),
    }


def _provider_non_authoritative(event: EconomicEvent, fare: FarePlan) -> bool:
    payload = event.payload
    return (
        payload.get("provider_status") == "authorized"
        and event.canonical_fare_hash == fare.fare_hash()
        and "trip_legitimacy" not in payload
        and "authoritative_fare" not in payload
    )


def _rejected_cases() -> tuple[str, ...]:
    rejected = []
    for case_name, attempt in (
        ("provider_authorization_defines_trip_truth", _reject_provider_trip_truth),
        ("provider_timestamp_defines_event_order", _reject_provider_timestamp_order),
        ("provider_fare_overrides_canonical_fare", _reject_provider_fare_override),
        ("client_fare_defines_truth", _reject_client_fare_truth),
        ("driver_commission_override_accepted", _reject_driver_commission_override),
        ("refund_mutation_rewrites_history", _reject_refund_mutation),
        ("fare_split_imbalance_accepted", _reject_split_imbalance),
        ("duplicate_payment_event_defines_truth", _reject_duplicate_payment_event),
    ):
        try:
            attempt()
        except EconomicTrustProofError:
            rejected.append(case_name)
        else:
            raise EconomicTrustProofError(f"economic authority case admitted: {case_name}")
    return tuple(rejected)


def _reject_provider_trip_truth() -> None:
    _normalize_economic_payload(
        {"provider_authorization_truth": "trip_valid", "provider_status": "authorized"}
    )


def _reject_provider_timestamp_order() -> None:
    _normalize_economic_payload(
        {"provider_timestamp_truth": "2026-05-26T00:00:00Z", "provider_status": "paid"}
    )


def _reject_provider_fare_override() -> None:
    _normalize_economic_payload({"authoritative_fare": "1.00", "provider_status": "paid"})


def _reject_client_fare_truth() -> None:
    _normalize_economic_payload({"client_fare_truth": "5.00", "client_id": "rider.001"})


def _reject_driver_commission_override() -> None:
    _normalize_economic_payload({"authoritative_commission": "99.00", "driver_id": "driver.001"})


def _reject_refund_mutation() -> None:
    _normalize_economic_payload({"authoritative_refund": "rewrite", "refund_id": "refund.001"})


def _reject_split_imbalance() -> None:
    _require_balanced_split(
        {
            "driver_share": "10.00",
            "platform_share": "3.00",
            "total": "14.00",
        }
    )


def _reject_duplicate_payment_event() -> None:
    event = _payment_authorization_event(
        FarePlan(
            ride_id="ride.duplicate.payment",
            distance_km=Decimal("1.00"),
            duration_minutes=Decimal("1.00"),
            base_fare=Decimal("4.20"),
            per_km_rate=Decimal("1.70"),
            per_minute_rate=Decimal("0.45"),
        )
    )
    _require_unique_economic_events((event, event))


def _normalize_economic_payload(payload: Mapping[str, Any]) -> dict[str, object]:
    _reject_authority_fields(payload)
    return {"payload": _canonicalize(payload)}


def _reject_authority_fields(value: Mapping[str, Any]) -> None:
    injected = FORBIDDEN_ECONOMIC_AUTHORITY_FIELDS.intersection(value.keys())
    if injected:
        raise EconomicTrustProofError(f"economic authority field: {sorted(injected)[0]}")
    for nested in value.values():
        if isinstance(nested, Mapping):
            _reject_authority_fields(nested)


def _require_balanced_split(split: Mapping[str, str]) -> None:
    total = _money(split["total"])
    driver_share = _money(split["driver_share"])
    platform_share = _money(split["platform_share"])
    if _money(driver_share + platform_share) != total:
        raise EconomicTrustProofError("fare split imbalance")


def _require_unique_economic_events(events: tuple[EconomicEvent, ...]) -> None:
    seen: set[str] = set()
    for event in events:
        event_hash = event.event_hash()
        if event_hash in seen:
            raise EconomicTrustProofError("duplicate payment event")
        seen.add(event_hash)


def _provider_reference(fare: FarePlan) -> str:
    return "provider.auth." + fare.fare_hash()[:24]


def _money(value: Decimal | int | str) -> Decimal:
    amount = Decimal(str(value))
    if amount < 0:
        raise EconomicTrustProofError("money value must be non-negative")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_text(value: Decimal) -> str:
    return format(value, ".2f")


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise EconomicTrustProofError(f"{field} must be non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise EconomicTrustProofError(f"{field} contains forbidden path syntax")
    return value


def _require_hash(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EconomicTrustProofError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise EconomicTrustProofError(f"{field} must be sha256") from exc
    return value


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
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

