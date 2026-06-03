from intelligence.demand_prediction import predict_zone_demand
from intelligence.surge_pricing import calculate_surge_multiplier

from .models import ServiceZone, ZoneDemandSnapshot


def create_service_zone(name, city, country):
    return ServiceZone.objects.create(
        name=name,
        city=city,
        country=country,
    )


def capture_zone_demand_snapshot(
    zone,
    historical_rides,
    active_requests,
    active_rides,
    available_drivers,
):
    prediction = predict_zone_demand(
        zone=zone,
        historical_rides=historical_rides,
        active_requests=active_requests,
    )
    surge_multiplier = calculate_surge_multiplier(
        predicted_demand=prediction["predicted_demand"],
        available_drivers=available_drivers,
    )

    return ZoneDemandSnapshot.objects.create(
        zone=zone,
        active_rides=active_rides,
        available_drivers=available_drivers,
        predicted_demand=prediction["predicted_demand"],
        surge_multiplier=surge_multiplier,
    )


def latest_zone_snapshot(zone):
    return ZoneDemandSnapshot.objects.filter(zone=zone).order_by("-captured_at").first()
