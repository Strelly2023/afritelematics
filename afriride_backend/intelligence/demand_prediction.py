def _count(value):
    if hasattr(value, "count"):
        return value.count()
    return len(value)


def predict_zone_demand(zone, historical_rides, active_requests):
    baseline = _count(historical_rides)
    current_pressure = _count(active_requests)
    predicted = baseline + current_pressure

    return {
        "zone_id": zone.id,
        "predicted_demand": predicted,
        "confidence": "bounded",
        "authority": "recommendation_only",
    }
