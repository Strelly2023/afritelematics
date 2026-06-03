from evidence.models import EventLog

from .regions import FailoverPolicy, Region


def resolve_failover_region(region):
    policy = FailoverPolicy.objects.filter(region=region, enabled=True).first()
    if policy is None:
        return None

    return Region.objects.filter(code=policy.backup_region, active=True).first()


def route_to_failover(region, reason, actor=None):
    backup = resolve_failover_region(region)
    if backup is None:
        return {
            "failover_available": False,
            "backup_region": None,
            "reason": "no_active_backup_region",
        }

    EventLog.objects.create(
        event_type="region_failover_routed",
        actor=actor,
        metadata={
            "region_id": region.id,
            "region_code": region.code,
            "backup_region_id": backup.id,
            "backup_region_code": backup.code,
            "reason": reason,
            "authority": "failover_projection",
        },
    )

    return {
        "failover_available": True,
        "backup_region": backup,
        "reason": reason,
    }
