from evidence.models import EventLog

from .models import PilotMetrics, PilotParticipant, PilotProgram


def register_pilot(name, city, start_date, end_date):
    pilot = PilotProgram.objects.create(
        name=name,
        city=city,
        start_date=start_date,
        end_date=end_date,
    )
    PilotMetrics.objects.create(pilot=pilot)

    EventLog.objects.create(
        event_type="pilot_registered",
        metadata={
            "pilot_id": pilot.id,
            "city": city,
            "status": pilot.status,
            "authority": "pilot_operations",
        },
    )

    return pilot


def add_pilot_participant(pilot, user, role):
    participant, _ = PilotParticipant.objects.update_or_create(
        pilot=pilot,
        user=user,
        role=role,
        defaults={"active": True},
    )

    EventLog.objects.create(
        event_type="pilot_participant_added",
        actor=user,
        metadata={
            "pilot_id": pilot.id,
            "participant_id": participant.id,
            "role": role,
        },
    )

    return participant


def update_pilot_status(pilot, status):
    pilot.status = status
    pilot.save(update_fields=["status"])

    EventLog.objects.create(
        event_type="pilot_status_updated",
        metadata={
            "pilot_id": pilot.id,
            "status": status,
        },
    )

    return pilot
