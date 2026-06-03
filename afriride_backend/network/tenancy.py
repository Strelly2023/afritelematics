from evidence.models import EventLog

from .regions import RegionOperator


def assign_region_operator(region, user, role, actor=None):
    assignment, _ = RegionOperator.objects.update_or_create(
        region=region,
        user=user,
        role=role,
        defaults={"active": True},
    )

    EventLog.objects.create(
        event_type="region_operator_assigned",
        actor=actor,
        metadata={
            "region_id": region.id,
            "region_code": region.code,
            "user_id": user.id,
            "role": role,
        },
    )

    return assignment


def user_regions(user):
    return RegionOperator.objects.filter(user=user, active=True).select_related("region")
