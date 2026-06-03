from .regions import Region


def resolve_region_for_city(country, city):
    return Region.objects.filter(
        country=country,
        city=city,
        active=True,
    ).first()


def route_request_to_region(country, city):
    region = resolve_region_for_city(country=country, city=city)
    if region is None:
        return {
            "routed": False,
            "reason": "no_active_region",
            "region": None,
        }

    return {
        "routed": True,
        "reason": None,
        "region": region,
    }
