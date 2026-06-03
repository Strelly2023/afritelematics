from evidence.models import EventLog
from route_replay.services import get_route_replay
from trust.services import apply_trust_event

from enforcement.actions import build_enforcement_recommendation

from .rules import evaluate_fraud_rules


def review_ride_integrity(ride):
    """Review replay-backed ride evidence and produce bounded trust signals."""

    replay_data = get_route_replay(ride.id)
    anomalies = evaluate_fraud_rules(replay_data)

    if anomalies:
        profile = apply_trust_event(
            user=ride.driver,
            ride=ride,
            event_type="fraud_flag",
            reason=str(anomalies),
        )
        enforcement = build_enforcement_recommendation(
            user=ride.driver,
            trust_profile=profile,
            ride=ride,
        )

        EventLog.objects.create(
            ride=ride,
            event_type="fraud_review_flagged",
            actor=ride.driver,
            metadata={
                "anomalies": anomalies,
                "authority": "manual_review_required",
            },
        )

        return {
            "integrity": "flagged",
            "anomalies": anomalies,
            "enforcement": enforcement,
            "authority": "manual_review_required",
        }

    profile = apply_trust_event(
        user=ride.driver,
        ride=ride,
        event_type="verified_clean_replay",
        reason="Replay completed without anomaly",
    )

    return {
        "integrity": "verified",
        "anomalies": [],
        "trust_score": profile.score,
        "authority": "clear",
    }
