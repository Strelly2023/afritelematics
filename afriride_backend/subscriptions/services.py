from evidence.models import EventLog

from .models import Subscription


def start_subscription(plan, organization=None, fleet=None, actor=None):
    if organization is None and fleet is None:
        raise ValueError("Subscription requires organization or fleet")
    if organization is not None and fleet is not None:
        raise ValueError("Subscription target must be organization or fleet, not both")

    subscription = Subscription.objects.create(
        organization=organization,
        fleet=fleet,
        plan=plan,
    )

    EventLog.objects.create(
        event_type="subscription_started",
        actor=actor,
        metadata={
            "subscription_id": subscription.id,
            "plan_id": plan.id,
            "organization_id": getattr(organization, "id", None),
            "fleet_id": getattr(fleet, "id", None),
        },
    )

    return subscription


def cancel_subscription(subscription, actor=None):
    subscription.status = "cancelled"
    subscription.save(update_fields=["status", "updated_at"])

    EventLog.objects.create(
        event_type="subscription_cancelled",
        actor=actor,
        metadata={"subscription_id": subscription.id},
    )

    return subscription


def has_active_subscription(organization=None, fleet=None):
    return Subscription.objects.filter(
        organization=organization,
        fleet=fleet,
        status="active",
    ).exists()
