from .calculator import calculate_fare
from .models import FarePolicy


def get_active_fare_policy():
    return FarePolicy.objects.filter(active=True).order_by("id").first()


def calculate_replay_backed_fare(replay_receipt, policy=None):
    """Calculate fare from a replay receipt or route replay receipt."""

    fare_policy = policy or get_active_fare_policy()
    if fare_policy is None:
        raise ValueError("No active fare policy available")

    return calculate_fare(
        distance_km=replay_receipt.get("distance_km", 0),
        duration_minutes=replay_receipt.get("duration_minutes", 0),
        policy=fare_policy,
    )
