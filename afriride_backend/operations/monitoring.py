from evidence.models import EventLog

from .noc import NetworkHealthSnapshot


def record_network_health(
    region,
    active_rides,
    replay_success_rate,
    payment_success_rate,
    uptime,
):
    snapshot = NetworkHealthSnapshot.objects.create(
        region=region,
        active_rides=active_rides,
        replay_success_rate=replay_success_rate,
        payment_success_rate=payment_success_rate,
        uptime=uptime,
    )

    EventLog.objects.create(
        event_type="network_health_snapshot_recorded",
        metadata={
            "region_id": region.id,
            "region_code": region.code,
            "snapshot_id": snapshot.id,
            "replay_success_rate": replay_success_rate,
            "payment_success_rate": payment_success_rate,
            "uptime": uptime,
        },
    )

    return snapshot


def latest_network_health(region):
    return NetworkHealthSnapshot.objects.filter(region=region).order_by("-created_at").first()
