"""Multi-region configuration, pricing, compliance, and branding."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from threading import RLock
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class PricingPolicy:
    currency: str
    base_minor: int
    per_km_minor: int
    per_minute_minor: int
    minimum_minor: int
    booking_fee_minor: int
    surge_cap: Decimal
    tax_rate: Decimal


@dataclass(frozen=True)
class RegionPolicy:
    region_id: str
    country_code: str
    name: str
    time_zone: str
    locales: tuple[str, ...]
    default_locale: str
    currency: str
    currency_minor_digits: int
    data_residency: str
    emergency_number: str
    compliance: tuple[str, ...]
    pricing: PricingPolicy


REGIONS: dict[str, RegionPolicy] = {
    "au-mel": RegionPolicy(
        "au-mel", "AU", "Melbourne", "Australia/Melbourne", ("en-AU",), "en-AU",
        "AUD", 2, "ap-southeast-2", "000",
        ("privacy_act_1988", "commercial_passenger_vehicle_victoria", "gst"),
        PricingPolicy("AUD", 450, 185, 55, 900, 75, Decimal("2.00"), Decimal("0.10")),
    ),
    "ug-kla": RegionPolicy(
        "ug-kla", "UG", "Kampala", "Africa/Kampala", ("en-UG", "sw-UG"), "en-UG",
        "UGX", 0, "africa-east", "999",
        ("data_protection_and_privacy_act_2019", "traffic_and_road_safety_act"),
        PricingPolicy("UGX", 3500, 1200, 180, 7000, 500, Decimal("2.50"), Decimal("0.00")),
    ),
    "ke-nbo": RegionPolicy(
        "ke-nbo", "KE", "Nairobi", "Africa/Nairobi", ("en-KE", "sw-KE"), "en-KE",
        "KES", 2, "africa-east", "999",
        ("data_protection_act_2019", "ntsa_transport_network_company_rules", "vat"),
        PricingPolicy("KES", 18000, 6500, 1200, 35000, 5000, Decimal("2.50"), Decimal("0.16")),
    ),
    "ng-los": RegionPolicy(
        "ng-los", "NG", "Lagos", "Africa/Lagos", ("en-NG",), "en-NG",
        "NGN", 2, "africa-west", "112",
        ("nigeria_data_protection_act_2023", "lagos_state_transport_rules", "vat"),
        PricingPolicy("NGN", 70000, 30000, 4500, 150000, 20000, Decimal("3.00"), Decimal("0.075")),
    ),
    "za-jnb": RegionPolicy(
        "za-jnb", "ZA", "Johannesburg", "Africa/Johannesburg", ("en-ZA", "zu-ZA"), "en-ZA",
        "ZAR", 2, "africa-south", "112",
        ("popia", "national_land_transport_act", "vat"),
        PricingPolicy("ZAR", 2500, 1200, 350, 6000, 500, Decimal("2.50"), Decimal("0.15")),
    ),
}

REQUIRED_DOCUMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    "AU": {"driver": ("driver_licence", "driver_accreditation", "vehicle_registration", "insurance")},
    "UG": {"driver": ("driving_permit", "vehicle_registration", "third_party_insurance")},
    "KE": {"driver": ("driving_licence", "psv_badge", "vehicle_inspection", "insurance")},
    "NG": {"driver": ("driving_licence", "lasdri_card", "roadworthiness", "insurance")},
    "ZA": {"driver": ("driving_licence", "professional_driving_permit", "roadworthy_certificate", "insurance")},
}


class GlobalReadinessService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._overrides: dict[str, dict[str, Any]] = self._load_overrides()

    def regions(self) -> list[dict[str, Any]]:
        return [self.region(region_id) for region_id in sorted(REGIONS)]

    def region(self, region_id: str) -> dict[str, Any]:
        try:
            policy = REGIONS[region_id]
        except KeyError as exc:
            raise KeyError("region_not_supported") from exc
        result = asdict(policy)
        result["pricing"]["surge_cap"] = str(policy.pricing.surge_cap)
        result["pricing"]["tax_rate"] = str(policy.pricing.tax_rate)
        return result

    def resolve(
        self,
        *,
        organization_id: str,
        region_id: str | None,
        locale: str | None,
    ) -> dict[str, Any]:
        selected = region_id or os.environ.get("AFRIRIDE_DEFAULT_REGION", "ug-kla")
        region = self.region(selected)
        allowed_locales = region["locales"]
        selected_locale = locale if locale in allowed_locales else region["default_locale"]
        brand = {
            "organization_id": organization_id,
            "name": "AfriRide",
            "short_name": "AfriRide",
            "primary_color": "#006B57",
            "support_url": "https://afritechnology.com/support",
            "logo_url": None,
        }
        with self._lock:
            override = self._overrides.get(organization_id, {})
        brand.update(override.get("brand", {}))
        if override.get("regions") and selected not in override["regions"]:
            raise PermissionError("region_not_enabled_for_organization")
        return {
            "contract": "afriride.global.v1",
            "region": region,
            "locale": selected_locale,
            "brand": brand,
            "server_time": self.localized_time(selected),
        }

    def quote(
        self,
        *,
        region_id: str,
        distance_km: Decimal,
        duration_minutes: Decimal,
        surge_multiplier: Decimal = Decimal("1"),
        vehicle_multiplier: Decimal = Decimal("1"),
    ) -> dict[str, Any]:
        region = REGIONS.get(region_id)
        if region is None:
            raise KeyError("region_not_supported")
        pricing = region.pricing
        surge = max(Decimal("1"), min(surge_multiplier, pricing.surge_cap))
        subtotal = (
            Decimal(pricing.base_minor)
            + distance_km * pricing.per_km_minor
            + duration_minutes * pricing.per_minute_minor
        )
        metered = max(Decimal(pricing.minimum_minor), subtotal * surge * vehicle_multiplier)
        before_tax = metered + pricing.booking_fee_minor
        tax = (before_tax * pricing.tax_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total = (before_tax + tax).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return {
            "region_id": region_id,
            "currency": pricing.currency,
            "currency_minor_digits": region.currency_minor_digits,
            "distance_km": str(distance_km),
            "duration_minutes": str(duration_minutes),
            "surge_multiplier": str(surge),
            "vehicle_multiplier": str(vehicle_multiplier),
            "subtotal_minor": int(metered),
            "booking_fee_minor": pricing.booking_fee_minor,
            "tax_minor": int(tax),
            "total_minor": int(total),
            "pricing_version": "global-2026-07-v1",
            "authority": "server_pricing_policy",
            "quoted_at": self.localized_time(region_id),
        }

    def localized_time(self, region_id: str, at: datetime | None = None) -> dict[str, str]:
        region = REGIONS.get(region_id)
        if region is None:
            raise KeyError("region_not_supported")
        instant = (at or datetime.now(UTC)).astimezone(UTC)
        return {
            "utc": instant.isoformat().replace("+00:00", "Z"),
            "local": instant.astimezone(ZoneInfo(region.time_zone)).isoformat(),
            "time_zone": region.time_zone,
        }

    def compliance_check(
        self, *, region_id: str, actor_type: str, documents: list[str]
    ) -> dict[str, Any]:
        region = REGIONS.get(region_id)
        if region is None:
            raise KeyError("region_not_supported")
        required = REQUIRED_DOCUMENTS.get(region.country_code, {}).get(actor_type, ())
        supplied = set(documents)
        missing = [document for document in required if document not in supplied]
        return {
            "region_id": region_id,
            "country_code": region.country_code,
            "actor_type": actor_type,
            "required_documents": list(required),
            "missing_documents": missing,
            "compliant": not missing,
            "dispatch_eligible": actor_type != "driver" or not missing,
            "policy_references": list(region.compliance),
            "authority": "regional_compliance_policy",
        }

    @staticmethod
    def _load_overrides() -> dict[str, dict[str, Any]]:
        raw = os.environ.get("AFRIRIDE_TENANT_CONFIG_JSON", "{}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("invalid_AFRIRIDE_TENANT_CONFIG_JSON") from exc
        if not isinstance(value, dict):
            raise RuntimeError("AFRIRIDE_TENANT_CONFIG_JSON_must_be_object")
        return value


global_readiness = GlobalReadinessService()
