from __future__ import annotations

from .models import TelemetryProfile


def verify_telemetry_profile(profile: TelemetryProfile, minimum_sample_size: int = 100) -> dict[str, object]:
    verified = bool(
        profile.sample_size >= minimum_sample_size
        and profile.fresh
        and profile.device_coverage
        and profile.network_coverage
        and profile.journey_coverage
        and profile.accessibility_coverage
        and profile.region_coverage
        and not profile.static_seed_only
    )
    return {
        "configured": True,
        "telemetry_connected": profile.sample_size > 0,
        "telemetry_fresh": profile.fresh,
        "verified": verified,
        "digital_twin_verified": verified,
    }
