from .adapters import build_journey_enrichment_payload
from .models import PublicTransportStop


def find_nearby_public_transport_stops(latitude, longitude, radius_km=2):
    """Placeholder for a future PostGIS distance query."""

    return []


def get_public_transport_enrichment(latitude, longitude, radius_km=2):
    stops = find_nearby_public_transport_stops(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
    return build_journey_enrichment_payload(stops)


def register_public_transport_stop(provider, name, latitude, longitude, external_id=""):
    return PublicTransportStop.objects.create(
        provider=provider,
        name=name,
        latitude=latitude,
        longitude=longitude,
        external_id=external_id,
    )
