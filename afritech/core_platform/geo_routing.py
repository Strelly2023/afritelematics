"""Geo-aware routing and latency tuning helpers for edge-native control planes."""

from __future__ import annotations

from typing import Any, Mapping


SUPPORTED_EDGE_REGIONS = ("AU", "EU", "US")

_COUNTRY_TO_REGION = {
    "AU": "AU",
    "NZ": "AU",
    "PG": "AU",
    "FJ": "AU",
    "WS": "AU",
    "TO": "AU",
    "KI": "AU",
    "SB": "AU",
    "VU": "AU",
    "NC": "AU",
    "PF": "AU",
    "CK": "AU",
    "TL": "AU",
    "DE": "EU",
    "FR": "EU",
    "IT": "EU",
    "ES": "EU",
    "PT": "EU",
    "NL": "EU",
    "BE": "EU",
    "LU": "EU",
    "IE": "EU",
    "GB": "EU",
    "UK": "EU",
    "SE": "EU",
    "NO": "EU",
    "FI": "EU",
    "DK": "EU",
    "IS": "EU",
    "PL": "EU",
    "CZ": "EU",
    "AT": "EU",
    "CH": "EU",
    "GR": "EU",
    "RO": "EU",
    "BG": "EU",
    "HU": "EU",
    "SK": "EU",
    "SI": "EU",
    "HR": "EU",
    "EE": "EU",
    "LV": "EU",
    "LT": "EU",
    "US": "US",
    "CA": "US",
    "MX": "US",
    "BR": "US",
    "AR": "US",
    "CL": "US",
    "CO": "US",
    "PE": "US",
    "CR": "US",
    "PA": "US",
    "GT": "US",
    "HN": "US",
    "SV": "US",
    "NI": "US",
    "DO": "US",
    "PR": "US",
}

_UNHEALTHY_STATUSES = {"down", "degraded", "unhealthy", "disabled", "critical"}


def _normalize_region(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_country(value: Any) -> str:
    return str(value or "").strip().upper()


def parse_region_health(raw: Mapping[str, Any] | str | None) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, Mapping):
        return {_normalize_region(key): str(value).strip().lower() for key, value in raw.items() if _normalize_region(key)}
    parsed: dict[str, str] = {}
    for chunk in str(raw).split(","):
        item = chunk.strip()
        if not item or ":" not in item:
            continue
        region, status = item.split(":", 1)
        region_key = _normalize_region(region)
        if region_key:
            parsed[region_key] = str(status).strip().lower()
    return parsed


def parse_latency_map(raw: Mapping[str, Any] | str | None) -> dict[str, int]:
    if raw is None:
        return {}
    if isinstance(raw, Mapping):
        parsed: dict[str, int] = {}
        for key, value in raw.items():
            region = _normalize_region(key)
            if not region:
                continue
            try:
                parsed[region] = max(0, int(value))
            except (TypeError, ValueError):
                continue
        return parsed
    parsed = {}
    for chunk in str(raw).split(","):
        item = chunk.strip()
        if not item or ":" not in item:
            continue
        region, latency = item.split(":", 1)
        region_key = _normalize_region(region)
        if not region_key:
            continue
        try:
            parsed[region_key] = max(0, int(float(latency)))
        except (TypeError, ValueError):
            continue
    return parsed


def country_to_region(country_code: str | None) -> str | None:
    country = _normalize_country(country_code)
    if not country:
        return None
    return _COUNTRY_TO_REGION.get(country)


def healthy_regions(health_map: Mapping[str, Any] | None) -> list[str]:
    health = {region: str(status).strip().lower() for region, status in (health_map or {}).items()}
    healthy = [region for region in SUPPORTED_EDGE_REGIONS if health.get(region, "healthy") not in _UNHEALTHY_STATUSES]
    return healthy or list(SUPPORTED_EDGE_REGIONS)


def latency_multiplier(latency_ms: int | None, trust_level: str | None = None) -> float:
    if latency_ms is None:
        return 1.0
    latency = max(0, int(latency_ms))
    elevated_trust = _normalize_region(trust_level) in {"ENTERPRISE", "REGULATOR"}
    if latency < 50:
        return 1.0
    if latency < 150:
        return 0.85 if elevated_trust else 0.7
    return 0.7 if elevated_trust else 0.5


def adjust_sla_capacity(base_limit: int, latency_ms: int | None, trust_level: str | None = None) -> int:
    multiplier = latency_multiplier(latency_ms, trust_level)
    return max(1, int(round(max(1, int(base_limit)) * multiplier)))


def select_region(
    *,
    client_country: str | None = None,
    client_region: str | None = None,
    preferred_region: str | None = None,
    trust_level: str | None = None,
    health_map: Mapping[str, Any] | None = None,
    latency_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_health = {region: str(status).strip().lower() for region, status in (health_map or {}).items()}
    normalized_latencies: dict[str, int] = {}
    for region, value in (latency_map or {}).items():
        region_key = _normalize_region(region)
        if not region_key:
            continue
        try:
            normalized_latencies[region_key] = max(0, int(value))
        except (TypeError, ValueError):
            continue

    healthy = healthy_regions(normalized_health)
    region_candidates = [region for region in SUPPORTED_EDGE_REGIONS if region in healthy] or list(SUPPORTED_EDGE_REGIONS)

    reason = "nearest_healthy_region"
    geo_source = "latency"

    for candidate in (preferred_region, client_region):
        normalized_candidate = _normalize_region(candidate)
        if normalized_candidate and normalized_candidate in region_candidates:
            selected = normalized_candidate
            reason = "requested_region" if normalized_candidate == _normalize_region(preferred_region) else "client_region"
            geo_source = "preferred" if normalized_candidate == _normalize_region(preferred_region) else "client"
            break
    else:
        mapped_region = country_to_region(client_country)
        if mapped_region and mapped_region in region_candidates:
            selected = mapped_region
            reason = "country_mapping"
            geo_source = "country"
        elif normalized_latencies:
            selected = min(
                region_candidates,
                key=lambda region: (
                    normalized_latencies.get(region, 10_000),
                    SUPPORTED_EDGE_REGIONS.index(region),
                ),
            )
            reason = "lowest_latency"
            geo_source = "latency"
        else:
            selected = region_candidates[0]
            reason = "first_healthy_region"
            geo_source = "health"

    failover_candidates = [region for region in region_candidates if region != selected]
    failover_region = failover_candidates[0] if failover_candidates else None
    selected_latency = normalized_latencies.get(selected)
    trust = str(trust_level or "").strip().lower() or "sandbox"
    effective_capacity_multiplier = latency_multiplier(selected_latency, trust)

    return {
        "region": selected,
        "failover_region": failover_region,
        "healthy_regions": region_candidates,
        "client_country": _normalize_country(client_country) or None,
        "client_region": _normalize_region(client_region) or None,
        "preferred_region": _normalize_region(preferred_region) or None,
        "trust_level": trust,
        "geo_source": geo_source,
        "routing_reason": reason,
        "latency_ms": selected_latency,
        "latency_map": {region: int(value) for region, value in normalized_latencies.items()},
        "health_map": {region: str(status).strip().lower() for region, status in normalized_health.items()},
        "sla_multiplier": effective_capacity_multiplier,
    }


__all__ = [
    "SUPPORTED_EDGE_REGIONS",
    "adjust_sla_capacity",
    "country_to_region",
    "healthy_regions",
    "latency_multiplier",
    "parse_latency_map",
    "parse_region_health",
    "select_region",
]
