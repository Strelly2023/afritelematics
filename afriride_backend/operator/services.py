from evidence.models import EventLog


def operator_event_stream(limit=100):
    """Return recent canonical events for operator display."""

    return EventLog.objects.order_by("-created_at")[:limit]


def replay_safe_operator_summary():
    """Summarize canonical events without granting operator override authority."""

    return {
        "authority": "observation_only",
        "event_count": EventLog.objects.count(),
    }
