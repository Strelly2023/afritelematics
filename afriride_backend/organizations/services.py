from evidence.models import EventLog

from .models import Organization, OrganizationMember


def create_organization(name, country, currency, billing_email, actor=None):
    organization = Organization.objects.create(
        name=name,
        country=country,
        currency=currency,
        billing_email=billing_email,
    )

    EventLog.objects.create(
        event_type="organization_created",
        actor=actor,
        metadata={
            "organization_id": organization.id,
            "country": country,
            "currency": currency,
        },
    )

    return organization


def add_organization_member(organization, user, role, actor=None):
    member, created = OrganizationMember.objects.update_or_create(
        organization=organization,
        user=user,
        defaults={"role": role, "active": True},
    )

    EventLog.objects.create(
        event_type="organization_member_added" if created else "organization_member_updated",
        actor=actor,
        metadata={
            "organization_id": organization.id,
            "user_id": user.id,
            "role": role,
        },
    )

    return member


def member_has_role(user, organization, role):
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        role=role,
        active=True,
    ).exists()
