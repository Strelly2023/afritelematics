from evidence.models import EventLog

from .guards import decide_enforcement_action, enforcement_boundary


def build_enforcement_recommendation(user, trust_profile, ride=None):
    action = decide_enforcement_action(
        trust_score=trust_profile.score,
        fraud_flags=trust_profile.fraud_flags,
    )
    boundary = enforcement_boundary(action)

    EventLog.objects.create(
        ride=ride,
        event_type="enforcement_recommendation_recorded",
        actor=user,
        metadata={
            "action": action,
            "trust_score": trust_profile.score,
            "fraud_flags": trust_profile.fraud_flags,
            "authority": boundary["authority"],
            "irreversible": boundary["irreversible"],
        },
    )

    return {
        "action": action,
        "boundary": boundary,
    }
