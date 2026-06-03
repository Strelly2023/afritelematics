def normalize_public_transport_stop(provider, raw_stop):
    return {
        "provider_id": provider.id,
        "provider_name": provider.name,
        "name": raw_stop.get("name"),
        "latitude": raw_stop.get("latitude"),
        "longitude": raw_stop.get("longitude"),
        "external_id": raw_stop.get("external_id", ""),
        "authority": "journey_enrichment_only",
    }


def build_journey_enrichment_payload(stops):
    return {
        "authority": "public_transport_enrichment_only",
        "stops": [
            {
                "stop_id": stop.id,
                "name": stop.name,
                "provider": stop.provider.name,
                "provider_type": stop.provider.provider_type,
                "latitude": float(stop.latitude),
                "longitude": float(stop.longitude),
            }
            for stop in stops
        ],
    }
