from evidence.models import EventLog

from .models import IntelligenceRecommendation


def record_recommendation(recommendation_type, payload, zone=None, ride=None, actor=None):
    recommendation = IntelligenceRecommendation.objects.create(
        recommendation_type=recommendation_type,
        zone=zone,
        ride=ride,
        payload=payload,
        authority=payload.get("authority", "recommendation_only"),
    )

    EventLog.objects.create(
        ride=ride,
        event_type="intelligence_recommendation_recorded",
        actor=actor,
        metadata={
            "recommendation_id": recommendation.id,
            "recommendation_type": recommendation_type,
            "authority": recommendation.authority,
        },
    )

    return recommendation
