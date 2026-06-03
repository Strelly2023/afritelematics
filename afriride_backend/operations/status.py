from network.regions import ExpansionCandidate, Region

from .incidents import Incident
from .noc import NetworkHealthSnapshot


def regional_status(region):
    health = (
        NetworkHealthSnapshot.objects.filter(region=region)
        .order_by("-created_at")
        .first()
    )
    open_incidents = Incident.objects.filter(region=region, resolved=False)

    return {
        "region_code": region.code,
        "country": region.country,
        "city": region.city,
        "active": region.active,
        "launched_at": region.launched_at.isoformat() if region.launched_at else None,
        "active_rides": health.active_rides if health else 0,
        "replay_success_rate": health.replay_success_rate if health else 0,
        "payment_success_rate": health.payment_success_rate if health else 0,
        "uptime": health.uptime if health else 0,
        "open_incidents": open_incidents.count(),
    }


def network_dashboard():
    regions = Region.objects.all().order_by("country", "city")
    active_regions = regions.filter(active=True)
    candidates = ExpansionCandidate.objects.filter(approved=False)
    latest_health = [
        NetworkHealthSnapshot.objects.filter(region=region)
        .order_by("-created_at")
        .first()
        for region in active_regions
    ]
    latest_health = [snapshot for snapshot in latest_health if snapshot is not None]

    replay_integrity = (
        round(
            sum(snapshot.replay_success_rate for snapshot in latest_health)
            / len(latest_health),
            2,
        )
        if latest_health
        else 0
    )
    payment_success = (
        round(
            sum(snapshot.payment_success_rate for snapshot in latest_health)
            / len(latest_health),
            2,
        )
        if latest_health
        else 0
    )

    return {
        "authority": "network_operations_projection",
        "regions_active": active_regions.count(),
        "replay_integrity": replay_integrity,
        "payment_success": payment_success,
        "open_incidents": Incident.objects.filter(resolved=False).count(),
        "expansion_candidates": candidates.count(),
        "regions": [regional_status(region) for region in regions],
    }
