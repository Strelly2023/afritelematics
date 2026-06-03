from evidence.models import EventLog

from .models import TrustEvent, TrustProfile
from .scoring import calculate_trust_delta, clamp_trust_score


def apply_trust_event(user, event_type, reason, ride=None):
    profile, _ = TrustProfile.objects.get_or_create(user=user)
    delta = calculate_trust_delta(event_type)

    profile.score = clamp_trust_score(profile.score + delta)

    if event_type == "ride_completed":
        profile.completed_rides += 1

    if event_type == "ride_cancelled":
        profile.cancelled_rides += 1

    if event_type == "fraud_flag":
        profile.fraud_flags += 1

    profile.save()

    trust_event = TrustEvent.objects.create(
        user=user,
        ride=ride,
        event_type=event_type,
        score_delta=delta,
        reason=reason,
    )

    EventLog.objects.create(
        ride=ride,
        event_type="trust_event_applied",
        actor=user,
        metadata={
            "trust_event_id": trust_event.id,
            "event_type": event_type,
            "score_delta": delta,
            "score": profile.score,
            "authority": "bounded_trust_signal",
        },
    )

    return profile
