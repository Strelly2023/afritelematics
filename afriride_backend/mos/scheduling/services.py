from .models import Journey, JourneySegment


def create_journey(user_id, metadata=None):
    return Journey.objects.create(
        user_id=user_id,
        metadata=metadata or {},
    )


def add_journey_segment(
    journey,
    segment_type,
    sequence,
    start_location,
    end_location,
    evidence_reference="",
):
    return JourneySegment.objects.create(
        journey=journey,
        segment_type=segment_type,
        sequence=sequence,
        start_location=start_location,
        end_location=end_location,
        evidence_reference=evidence_reference,
    )


def journey_projection(journey):
    return {
        "authority": "journey_coordination_projection",
        "journey_id": str(journey.journey_id),
        "status": journey.status,
        "segments": [
            {
                "segment_type": segment.segment_type,
                "sequence": segment.sequence,
                "start_location": segment.start_location,
                "end_location": segment.end_location,
                "evidence_reference": segment.evidence_reference,
                "replay_verified": segment.replay_verified,
            }
            for segment in journey.segments.all().order_by("sequence")
        ],
    }
